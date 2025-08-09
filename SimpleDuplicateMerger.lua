--[[
Simple Duplicate Merger Plugin for Family Historian
Finds duplicate individuals by surname batch and opens Merge/Compare
Simplified version focused on core functionality
]]--

require("iuplua")

local SimpleDuplicateMerger = {}

-- Plugin info
SimpleDuplicateMerger.Title = "Simple Duplicate Merger"
SimpleDuplicateMerger.Version = "1.0"
SimpleDuplicateMerger.Description = "Find duplicates by surname and step through Merge/Compare dialogs"

-- Simple settings
local BIRTH_WINDOW = 5  -- years
local MIN_SCORE = 60
local MAX_PAIRS = 1000

-- State
local current_pairs = {}
local handled_pairs = {}
local ui = {}

-- Utils
local function normalize_name(name)
    if not name then return "" end
    return name:upper():gsub("[^A-Z ]", ""):gsub("%s+", " "):match("^%s*(.-)%s*$")
end

local function soundex(name)
    if not name or name == "" then return "0000" end
    name = normalize_name(name)
    if name == "" then return "0000" end
    
    local first = name:sub(1, 1)
    name = name:gsub("[BFPV]", "1"):gsub("[CGJKQSXZ]", "2"):gsub("[DT]", "3")
             :gsub("[L]", "4"):gsub("[MN]", "5"):gsub("[R]", "6")
             :gsub("[AEIOUHWY]", ""):gsub("(%d)%d*%1", "%1")
    
    name = first .. name:sub(2):sub(1, 3)
    return (name .. "000"):sub(1, 4)
end

local function get_birth_year(indi_ptr)
    local birth = fhGetItemPtr(indi_ptr, "BIRT")
    if not birth then return nil end
    local date = fhGetItemPtr(birth, "DATE")
    if not date then return nil end
    local date_str = fhGetValueForItem(date)
    if not date_str then return nil end
    local year = date_str:match("(%d%d%d%d)")
    return year and tonumber(year) or nil
end

local function get_person_data(indi_ptr)
    local name_rec = fhGetItemPtr(indi_ptr, "NAME")
    if not name_rec then return nil end
    
    local given = fhGetValueForItem(name_rec, "GIVN") or ""
    local surname = fhGetValueForItem(name_rec, "SURN") or ""
    local full_name = fhGetDisplayText(name_rec)
    
    return {
        ptr = indi_ptr,
        id = fhGetRecordId(indi_ptr),
        given = given,
        surname = surname,
        full_name = full_name,
        birth_year = get_birth_year(indi_ptr),
        surname_norm = normalize_name(surname),
        given_norm = normalize_name(given),
        given_soundex = soundex(given)
    }
end

local function calculate_score(p1, p2)
    local score = 0
    
    -- Same given name (pre-filtered, so guaranteed)
    score = score + 40
    
    -- Surname comparison (if they exist)
    if p1.surname_norm ~= "" and p2.surname_norm ~= "" then
        if p1.surname_norm == p2.surname_norm then
            score = score + 20
        elseif soundex(p1.surname_norm) == soundex(p2.surname_norm) then
            score = score + 10
        end
    end
    
    -- Birth year comparison
    if p1.birth_year and p2.birth_year then
        local diff = math.abs(p1.birth_year - p2.birth_year)
        if diff == 0 then
            score = score + 20
        elseif diff <= 2 then
            score = score + 10
        elseif diff <= BIRTH_WINDOW then
            score = score + 5
        end
    end
    
    return score
end

local function find_duplicates_for_given_name(given_name)
    local people = {}
    local indi_ptr = fhGetFirstItem("INDI")
    
    -- Collect all people with this given name
    while indi_ptr do
        local person = get_person_data(indi_ptr)
        if person and person.given_norm == normalize_name(given_name) then
            table.insert(people, person)
        end
        indi_ptr = fhGetNextItem(indi_ptr)
    end
    
    -- Find pairs
    local pairs = {}
    for i = 1, #people - 1 do
        for j = i + 1, #people do
            local score = calculate_score(people[i], people[j])
            if score >= MIN_SCORE then
                local key = people[i].id .. ":" .. people[j].id
                if not handled_pairs[key] then
                    table.insert(pairs, {
                        person1 = people[i],
                        person2 = people[j],
                        score = score,
                        key = key
                    })
                end
            end
        end
    end
    
    -- Sort by score
    table.sort(pairs, function(a, b) return a.score > b.score end)
    
    -- Limit results
    if #pairs > MAX_PAIRS then
        local limited = {}
        for i = 1, MAX_PAIRS do
            table.insert(limited, pairs[i])
        end
        pairs = limited
    end
    
    return pairs
end

local function update_list()
    if not ui.matrix then return end
    
    ui.matrix.numlin = #current_pairs
    
    for i, pair in ipairs(current_pairs) do
        iup.SetAttribute(ui.matrix, i..":1", tostring(pair.score))
        iup.SetAttribute(ui.matrix, i..":2", pair.person1.full_name)
        iup.SetAttribute(ui.matrix, i..":3", pair.person1.birth_year and tostring(pair.person1.birth_year) or "")
        iup.SetAttribute(ui.matrix, i..":4", pair.person2.full_name)
        iup.SetAttribute(ui.matrix, i..":5", pair.person2.birth_year and tostring(pair.person2.birth_year) or "")
    end
    
    iup.Refresh(ui.matrix)
end

local function get_selected_pair()
    if not ui.matrix then return nil end
    local lin = tonumber(iup.GetAttribute(ui.matrix, "FOCUSCELL"):match("(%d+):"))
    if lin and lin > 0 and lin <= #current_pairs then
        return current_pairs[lin]
    end
    return nil
end

local function open_merge(pair)
    if not pair then return end
    
    -- Mark as handled
    handled_pairs[pair.key] = true
    
    -- Show instructions (since direct API call might not work)
    local msg = string.format([[
Ready to merge:

Person 1: %s (ID: %s)
Person 2: %s (ID: %s)

Instructions:
1. Click OK to continue
2. Go to Edit → Merge/Compare Records
3. Find person 2 in the list and click Compare
4. Review the merge and click Merge if correct

The pair will be removed from this list.]], 
        pair.person1.full_name, pair.person1.id,
        pair.person2.full_name, pair.person2.id)
    
    iup.Message("Merge Instructions", msg)
    
    -- Try to set focus to person 1
    fhSetCurrentRecord(pair.person1.ptr)
    
    -- Remove from list
    for i = #current_pairs, 1, -1 do
        if current_pairs[i].key == pair.key then
            table.remove(current_pairs, i)
            break
        end
    end
    
    update_list()
end

local function skip_pair(pair)
    if not pair then return end
    
    -- Just mark as handled
    handled_pairs[pair.key] = true
    
    -- Remove from list
    for i = #current_pairs, 1, -1 do
        if current_pairs[i].key == pair.key then
            table.remove(current_pairs, i)
            break
        end
    end
    
    update_list()
end

local function search_surname()
    local surname = ui.surname_text.value
    if not surname or surname == "" then
        iup.Message("Error", "Please enter a surname to search")
        return
    end
    
    ui.status.title = "Searching for duplicates..."
    iup.Refresh(ui.status)
    
    current_pairs = find_duplicates_for_surname(surname)
    update_list()
    
    ui.status.title = string.format("Found %d potential duplicates for '%s'", #current_pairs, surname)
end

local function create_ui()
    -- Input
    ui.surname_text = iup.text{size = "200x"}
    local search_btn = iup.button{title = "Search", action = search_surname}
    
    -- Results list
    ui.matrix = iup.matrix{
        numcol = 5,
        numlin = 0,
        widthdef = "100"
    }
    
    -- Set headers
    iup.SetAttribute(ui.matrix, "0:1", "Score")
    iup.SetAttribute(ui.matrix, "0:2", "Person 1")
    iup.SetAttribute(ui.matrix, "0:3", "Birth 1")
    iup.SetAttribute(ui.matrix, "0:4", "Person 2")
    iup.SetAttribute(ui.matrix, "0:5", "Birth 2")
    
    -- Control buttons
    local merge_btn = iup.button{title = "Open Merge", 
                                action = function() open_merge(get_selected_pair()) end}
    local skip_btn = iup.button{title = "Skip This Pair", 
                               action = function() skip_pair(get_selected_pair()) end}
    
    -- Status
    ui.status = iup.label{title = "Enter surname and click Search"}
    
    -- Double-click to merge
    ui.matrix.dblclick_cb = function() open_merge(get_selected_pair()) end
    
    -- Main dialog
    local dialog = iup.dialog{
        iup.vbox{
            iup.hbox{
                iup.label{title = "Surname:"}, ui.surname_text, search_btn
            },
            ui.matrix,
            iup.hbox{
                merge_btn, skip_btn,
                iup.fill{},
                iup.button{title = "Close", action = function() return iup.CLOSE end}
            },
            ui.status
        },
        title = "Simple Duplicate Merger",
        size = "700x500"
    }
    
    return dialog
end

-- Main function
function SimpleDuplicateMerger.Main()
    if not fhGetCurrentProject() then
        iup.Message("Error", "No project is currently open.")
        return
    end
    
    local dialog = create_ui()
    dialog:popup(iup.CENTER, iup.CENTER)
    dialog:destroy()
end

-- Register
fhRegisterPlugin(SimpleDuplicateMerger)