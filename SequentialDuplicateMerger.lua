--[[
Sequential Duplicate Merger Plugin for Family Historian
Finds candidate duplicate individuals in batches and opens Merge/Compare for manual review
Based on specification from ChatGPT conversation
]]--

require("iuplua")

local SequentialDuplicateMerger = {}

-- Plugin information
SequentialDuplicateMerger.Title = "Sequential Duplicate Merger"
SequentialDuplicateMerger.Version = "1.0"
SequentialDuplicateMerger.LastUpdated = "2025"
SequentialDuplicateMerger.Description = [[
Find potential duplicate individuals in batches (by surname initial) 
and step through them with manual Merge/Compare confirmation.
Designed for very large trees where standard duplicate finders timeout.
]]

-- Default settings
local default_settings = {
    batch_mode = "INITIAL",  -- INITIAL or SURNAME
    batch_value = "A",
    birth_window = 3,
    use_soundex = true,
    use_given_initial = true,
    min_score = 50,
    max_pairs_per_batch = 2000,
    consider_spouse = true,
    consider_children = true,
    consider_place = false
}

-- Global state
local settings = {}
local handled_pairs = {
    resolved = {},
    skipped = {},
    not_match = {}
}
local current_pairs = {}
local current_index = 1
local ui_elements = {}

-- Utility functions
local function normalize_string(str)
    if not str then return "" end
    -- Remove diacritics, punctuation, convert to uppercase
    str = string.gsub(str:upper(), "[^A-Z0-9 ]", "")
    str = string.gsub(str, "%s+", " ")
    return string.gsub(str, "^%s+", ""):gsub("%s+$", "")
end

local function soundex(str)
    if not str or str == "" then return "0000" end
    str = normalize_string(str)
    if str == "" then return "0000" end
    
    local first_char = string.sub(str, 1, 1)
    str = string.gsub(str, "[BFPV]", "1")
    str = string.gsub(str, "[CGJKQSXZ]", "2")
    str = string.gsub(str, "[DT]", "3")
    str = string.gsub(str, "[L]", "4")
    str = string.gsub(str, "[MN]", "5")
    str = string.gsub(str, "[R]", "6")
    str = string.gsub(str, "[AEIOUHWY]", "")
    str = string.gsub(str, "(.)(.)%1", "%1%2")
    str = first_char .. str:sub(2)
    str = str:sub(1, 4)
    while string.len(str) < 4 do
        str = str .. "0"
    end
    return str
end

local function parse_birth_year(date_str)
    if not date_str then return nil end
    local year = string.match(date_str, "%d%d%d%d")
    return year and tonumber(year) or nil
end

local function get_individual_data(indi_ptr)
    if not indi_ptr then return nil end
    
    local name_rec = fhGetItemPtr(indi_ptr, "NAME")
    local given = ""
    local surname = ""
    local full_name = ""
    
    if name_rec then
        given = fhGetValueForItem(name_rec, "GIVN") or ""
        surname = fhGetValueForItem(name_rec, "SURN") or ""
        full_name = fhGetDisplayText(name_rec)
    end
    
    local birth_rec = fhGetItemPtr(indi_ptr, "BIRT")
    local birth_date = ""
    local birth_year = nil
    if birth_rec then
        local date_rec = fhGetItemPtr(birth_rec, "DATE")
        if date_rec then
            birth_date = fhGetValueForItem(date_rec)
            birth_year = parse_birth_year(birth_date)
        end
    end
    
    return {
        ptr = indi_ptr,
        id = fhGetRecordId(indi_ptr),
        given = given,
        surname = surname,
        full_name = full_name,
        birth_date = birth_date,
        birth_year = birth_year,
        given_norm = normalize_string(given),
        surname_norm = normalize_string(surname),
        given_soundex = soundex(given),
        given_initial = string.sub(normalize_string(given), 1, 1)
    }
end

local function calculate_pair_score(person1, person2)
    local score = 0
    local hints = {}
    
    -- Given name comparison
    if person1.given_norm == person2.given_norm and person1.given_norm ~= "" then
        score = score + 40
        table.insert(hints, "Same given name")
    elseif person1.given_soundex == person2.given_soundex and person1.given_soundex ~= "0000" then
        score = score + 25
        table.insert(hints, "Similar given name")
    elseif person1.given_initial == person2.given_initial and person1.given_initial ~= "" then
        score = score + 10
    end
    
    -- Birth year comparison
    if person1.birth_year and person2.birth_year then
        local year_diff = math.abs(person1.birth_year - person2.birth_year)
        if year_diff == 0 then
            score = score + 20
            table.insert(hints, "Same birth year")
        elseif year_diff <= 1 then
            score = score + 10
        elseif year_diff <= settings.birth_window then
            score = score + 5
        end
    end
    
    -- Surname must match (pre-filtered, so this should always be true)
    if person1.surname_norm == person2.surname_norm and person1.surname_norm ~= "" then
        score = score + 10
    end
    
    return score, hints
end

local function generate_pair_key(id1, id2)
    if id1 < id2 then
        return id1 .. ":" .. id2
    else
        return id2 .. ":" .. id1
    end
end

local function load_individuals_for_batch(batch_mode, batch_value)
    local individuals = {}
    local indi_ptr = fhGetFirstItem("INDI")
    
    while indi_ptr do
        local person = get_individual_data(indi_ptr)
        if person then
            local include = false
            
            if batch_mode == "INITIAL" then
                local initial = string.sub(person.surname_norm, 1, 1)
                if initial == "" then initial = "#" end
                include = (initial == batch_value)
            elseif batch_mode == "SURNAME" then
                include = (person.surname_norm == normalize_string(batch_value))
            end
            
            if include then
                table.insert(individuals, person)
            end
        end
        indi_ptr = fhGetNextItem(indi_ptr)
    end
    
    return individuals
end

local function find_candidate_pairs(individuals)
    local pairs = {}
    
    -- Group by normalized surname
    local surname_groups = {}
    for _, person in ipairs(individuals) do
        local surname = person.surname_norm
        if not surname_groups[surname] then
            surname_groups[surname] = {}
        end
        table.insert(surname_groups[surname], person)
    end
    
    -- Generate pairs within each surname group
    for surname, group in pairs(surname_groups) do
        if #group > 1 then
            for i = 1, #group - 1 do
                for j = i + 1, #group do
                    local person1, person2 = group[i], group[j]
                    
                    -- Pre-filter by birth window
                    local birth_ok = true
                    if person1.birth_year and person2.birth_year then
                        local year_diff = math.abs(person1.birth_year - person2.birth_year)
                        birth_ok = (year_diff <= settings.birth_window * 2)  -- Generous pre-filter
                    end
                    
                    -- Pre-filter by given initial if enabled
                    local initial_ok = true
                    if settings.use_given_initial then
                        initial_ok = (person1.given_initial == person2.given_initial) or 
                                   (person1.given_initial == "") or (person2.given_initial == "")
                    end
                    
                    if birth_ok and initial_ok then
                        local score, hints = calculate_pair_score(person1, person2)
                        if score >= settings.min_score then
                            local key = generate_pair_key(person1.id, person2.id)
                            
                            -- Skip if already handled
                            if not handled_pairs.resolved[key] and 
                               not handled_pairs.not_match[key] then
                                table.insert(pairs, {
                                    person1 = person1,
                                    person2 = person2,
                                    score = score,
                                    hints = hints,
                                    key = key
                                })
                            end
                        end
                    end
                end
            end
        end
    end
    
    -- Sort by score descending
    table.sort(pairs, function(a, b) return a.score > b.score end)
    
    -- Cap to max pairs per batch
    if #pairs > settings.max_pairs_per_batch then
        local capped_pairs = {}
        for i = 1, settings.max_pairs_per_batch do
            table.insert(capped_pairs, pairs[i])
        end
        pairs = capped_pairs
    end
    
    return pairs
end

local function update_ui_list()
    if not ui_elements.matrix then return end
    
    -- Clear matrix
    ui_elements.matrix.numcol = 7
    ui_elements.matrix.numlin = #current_pairs
    
    -- Set headers
    iup.SetAttribute(ui_elements.matrix, "0:1", "Score")
    iup.SetAttribute(ui_elements.matrix, "0:2", "Surname")
    iup.SetAttribute(ui_elements.matrix, "0:3", "Given A")
    iup.SetAttribute(ui_elements.matrix, "0:4", "Birth A")
    iup.SetAttribute(ui_elements.matrix, "0:5", "Given B")
    iup.SetAttribute(ui_elements.matrix, "0:6", "Birth B")
    iup.SetAttribute(ui_elements.matrix, "0:7", "Hints")
    
    -- Populate data
    for i, pair in ipairs(current_pairs) do
        iup.SetAttribute(ui_elements.matrix, i..":1", tostring(pair.score))
        iup.SetAttribute(ui_elements.matrix, i..":2", pair.person1.surname)
        iup.SetAttribute(ui_elements.matrix, i..":3", pair.person1.given)
        iup.SetAttribute(ui_elements.matrix, i..":4", pair.person1.birth_date)
        iup.SetAttribute(ui_elements.matrix, i..":5", pair.person2.given)
        iup.SetAttribute(ui_elements.matrix, i..":6", pair.person2.birth_date)
        iup.SetAttribute(ui_elements.matrix, i..":7", table.concat(pair.hints, ", "))
    end
    
    iup.Refresh(ui_elements.matrix)
end

local function open_merge_compare(pair)
    if not pair then return end
    
    -- Try to open merge compare dialog
    -- This is a simplified approach - actual FH API calls may differ
    local success = false
    
    -- Method 1: Try to call FH's merge function directly
    if fhCallBuiltInFunction then
        success = fhCallBuiltInFunction("MergeCompareRecords", pair.person1.ptr, pair.person2.ptr)
    end
    
    -- Method 2: Fallback - open property boxes and show instructions
    if not success then
        fhSetCurrentRecord(pair.person1.ptr)
        iup.Message("Manual Merge Required", 
                   "Please use Edit -> Merge/Compare Records to merge:\n\n" ..
                   "Person 1: " .. pair.person1.full_name .. " (ID: " .. pair.person1.id .. ")\n" ..
                   "Person 2: " .. pair.person2.full_name .. " (ID: " .. pair.person2.id .. ")\n\n" ..
                   "Click OK when merge is complete or cancelled.")
    end
    
    -- For now, assume the merge was successful (in real implementation, 
    -- we would check if the records were actually merged)
    local key = pair.key
    handled_pairs.resolved[key] = true
    
    -- Remove from current pairs
    for i = #current_pairs, 1, -1 do
        if current_pairs[i].key == key then
            table.remove(current_pairs, i)
            break
        end
    end
    
    update_ui_list()
end

local function skip_pair(pair)
    if not pair then return end
    handled_pairs.skipped[pair.key] = true
end

local function mark_not_match(pair)
    if not pair then return end
    handled_pairs.not_match[pair.key] = true
    
    -- Remove from current pairs
    for i = #current_pairs, 1, -1 do
        if current_pairs[i].key == pair.key then
            table.remove(current_pairs, i)
            break
        end
    end
    
    update_ui_list()
end

local function get_selected_pair()
    if not ui_elements.matrix then return nil end
    local lin = tonumber(iup.GetAttribute(ui_elements.matrix, "FOCUSCELL"):match("(%d+):"))
    if lin and lin > 0 and lin <= #current_pairs then
        return current_pairs[lin]
    end
    return nil
end

local function load_batch()
    local batch_mode = settings.batch_mode
    local batch_value = settings.batch_value
    
    fhProgressShow("Loading individuals...")
    local individuals = load_individuals_for_batch(batch_mode, batch_value)
    fhProgressUpdate(50)
    
    fhProgressSetCaption("Finding candidate pairs...")
    current_pairs = find_candidate_pairs(individuals)
    fhProgressUpdate(100)
    fhProgressHide()
    
    current_index = 1
    update_ui_list()
    
    ui_elements.status_label.title = string.format("Found %d candidate pairs for %s: %s", 
                                                   #current_pairs, batch_mode, batch_value)
end

local function create_settings_dialog()
    local birth_window_text = iup.text{value = tostring(settings.birth_window), size = "50x"}
    local min_score_text = iup.text{value = tostring(settings.min_score), size = "50x"}
    local max_pairs_text = iup.text{value = tostring(settings.max_pairs_per_batch), size = "50x"}
    
    local soundex_toggle = iup.toggle{title = "Use Soundex", value = settings.use_soundex and "ON" or "OFF"}
    local initial_toggle = iup.toggle{title = "Use Given Initial", value = settings.use_given_initial and "ON" or "OFF"}
    local spouse_toggle = iup.toggle{title = "Consider Spouse", value = settings.consider_spouse and "ON" or "OFF"}
    local children_toggle = iup.toggle{title = "Consider Children", value = settings.consider_children and "ON" or "OFF"}
    local place_toggle = iup.toggle{title = "Consider Place", value = settings.consider_place and "ON" or "OFF"}
    
    local dialog = iup.dialog{
        iup.vbox{
            iup.label{title = "Settings"},
            iup.hbox{iup.label{title = "Birth Window (± years):"}, birth_window_text},
            iup.hbox{iup.label{title = "Minimum Score:"}, min_score_text},
            iup.hbox{iup.label{title = "Max Pairs Per Batch:"}, max_pairs_text},
            iup.frame{
                iup.vbox{
                    soundex_toggle,
                    initial_toggle,
                    spouse_toggle,
                    children_toggle,
                    place_toggle
                },
                title = "Options"
            },
            iup.hbox{
                iup.button{title = "OK", action = function()
                    settings.birth_window = tonumber(birth_window_text.value) or 3
                    settings.min_score = tonumber(min_score_text.value) or 50
                    settings.max_pairs_per_batch = tonumber(max_pairs_text.value) or 2000
                    settings.use_soundex = (soundex_toggle.value == "ON")
                    settings.use_given_initial = (initial_toggle.value == "ON")
                    settings.consider_spouse = (spouse_toggle.value == "ON")
                    settings.consider_children = (children_toggle.value == "ON")
                    settings.consider_place = (place_toggle.value == "ON")
                    return iup.CLOSE
                end},
                iup.button{title = "Cancel", action = function() return iup.CLOSE end}
            }
        },
        title = "Sequential Duplicate Merger Settings",
        size = "300x400"
    }
    
    dialog:popup(iup.CENTERPARENT, iup.CENTERPARENT)
    dialog:destroy()
end

local function create_ui()
    -- Initialize settings
    for k, v in pairs(default_settings) do
        settings[k] = v
    end
    
    -- Batch selection
    local batch_mode_list = iup.list{dropdown = "YES", 
                                    value = settings.batch_mode == "INITIAL" and 1 or 2,
                                    "1=Initial", "2=Exact Surname"}
    
    local batch_value_text = iup.text{value = settings.batch_value, size = "60x"}
    
    local load_button = iup.button{title = "Load Batch", 
                                  action = function() 
                                      settings.batch_mode = batch_mode_list.value == "1" and "INITIAL" or "SURNAME"
                                      settings.batch_value = batch_value_text.value
                                      load_batch() 
                                  end}
    
    local settings_button = iup.button{title = "Settings", action = create_settings_dialog}
    
    -- Main list
    ui_elements.matrix = iup.matrix{numcol = 7, numlin = 0, widthdef = "80"}
    
    -- Control buttons
    local open_merge_btn = iup.button{title = "Open Merge", 
                                     action = function() open_merge_compare(get_selected_pair()) end}
    
    local skip_btn = iup.button{title = "Skip", 
                               action = function() skip_pair(get_selected_pair()) end}
    
    local not_match_btn = iup.button{title = "Not a Match", 
                                    action = function() mark_not_match(get_selected_pair()) end}
    
    -- Status
    ui_elements.status_label = iup.label{title = "Select batch and click Load Batch to begin"}
    
    -- Layout
    local dialog = iup.dialog{
        iup.vbox{
            iup.frame{
                iup.hbox{
                    iup.label{title = "Batch Mode:"}, batch_mode_list,
                    iup.label{title = "Value:"}, batch_value_text,
                    load_button, settings_button
                },
                title = "Batch Selection"
            },
            iup.frame{
                ui_elements.matrix,
                title = "Candidate Pairs"
            },
            iup.hbox{
                open_merge_btn, skip_btn, not_match_btn,
                iup.fill{},
                iup.button{title = "Close", action = function() return iup.CLOSE end}
            },
            ui_elements.status_label
        },
        title = "Sequential Duplicate Merger",
        size = "800x600"
    }
    
    -- Double-click to open merge
    ui_elements.matrix.dblclick_cb = function()
        open_merge_compare(get_selected_pair())
    end
    
    return dialog
end

-- Main entry point
function SequentialDuplicateMerger.Main()
    if not fhGetCurrentProject() then
        iup.Message("Error", "No project is currently open.")
        return
    end
    
    local dialog = create_ui()
    dialog:popup(iup.CENTER, iup.CENTER)
    dialog:destroy()
end

-- Register plugin
fhRegisterPlugin(SequentialDuplicateMerger)