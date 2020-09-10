using System;
using System.IO;

namespace Kinship
{
    public class FamilyTerms
    {
        public string Ego { get; private set; }
        public string Father { get; private set; }
        public string Mother { get; private set; }
        public string Brother { get; private set; }
        public string Sister { get; private set; }
        public string Son { get; private set; }
        public string Daughter { get; private set; }
        public string Partner { get; private set; }
        public string Error { get; private set; }
        public string GrandFather { get; private set; }
        public string Nanna { get; private set; }
        public string Faedro { get; private set; }
        public string Aunt { get; private set; }
        public string AgnaticBrother { get; private set; }
        public string AgnaticSister { get; private set; }
        public string StepMother { get; private set; }
        public string GenGen { get; private set; }
        public string GrandMother { get; private set; }
        public string Uncle { get; private set; }
        public string Modrie { get; private set; }
        public string UterineBrother { get; private set; }
        public string UterineSister { get; private set; }
        public string StepFather { get; private set; }
        public string Nephew { get; private set; }
        public string Niece { get; private set; }
        public string Jeneter { get; private set; }
        public string Mitling { get; private set; }
        public string Mitolin { get; private set; }
        public string Levir { get; private set; }
        public string Wife { get; private set; }
        public string GrandSon { get; private set; }
        public string PaternalGranddaughter { get; private set; }
        public string Schnerre { get; private set; }
        public string DaughterSon { get; private set; }
        public string GrandDaughter { get; private set; }
        public string Yerno { get; private set; }
        public string Sweger { get; private set; }
        public string Swegra { get; private set; }
        public string StepSon { get; private set; }
        public string StepDaughter { get; private set; }
        public string AgnaticParallelCousin { get; private set; }
        public string AgnaticParallelCousinf { get; private set; }
        public string Gallen { get; private set; }
        public string Eame { get; private set; }
        public string HalfNephew { get; private set; }
        public string HalfNiece { get; private set; }
        public string StepMothersFather { get; private set; }
        public string StepMothersMother { get; private set; }
        public string StepBrother { get; private set; }
        public string StepSister { get; private set; }
        public string MothersAgnaticBrother { get; private set; }
        public string MothersAgnaticSister { get; private set; }
        public string StepYerno { get; private set; }
        public string Macheton { get; private set; }
        public string Machetonie { get; private set; }
        public string StepGrandDaughter { get; private set; }
        public string StepGrandMother { get; private set; }
        public string HalfModrie { get; private set; }
        public string StepGrandFather { get; private set; }
        public string BrotherSonDaughter { get; private set; }

        public string GetRelationship(string RelationshipString)
        {
            switch (RelationshipString.Length)
            {
                case 0:
                    return Ego;
                case 1:
                    switch (RelationshipString[0])
                    {
                        case 'F':
                            return Father;
                        case 'M':
                            return Mother;
                        case 'B':
                            return Brother;
                        case 'Z':
                            return Sister;
                        case 'S':
                            return Son;
                        case 'D':
                            return Daughter;
                        case 'P':
                            return Partner;
                        default:
                            return Error;
                    }
                case 2:
                    switch (RelationshipString)
                    {
                        case "FF": return GrandFather;
                        case "FM": return Nanna;
                        case "FB": return Faedro;
                        case "FZ": return Aunt;
                        case "FS": return AgnaticBrother;
                        case "FD": return AgnaticSister;
                        case "FP": return StepMother;
                        case "MF": return GenGen;
                        case "MM": return GrandMother;
                        case "MB": return Uncle;
                        case "MZ": return Modrie;
                        case "MS": return UterineBrother;
                        case "MD": return UterineSister;
                        case "MP": return StepFather;
                        case "BF": return Father;
                        case "BM": return Mother;
                        case "BB": return Brother;
                        case "BZ": return Sister;
                        case "BS": return Nephew;
                        case "BD": return Niece;
                        case "BP": return Jeneter;
                        case "ZF": return Father;
                        case "ZM": return Mother;
                        case "ZB": return Brother;
                        case "ZZ": return Sister;
                        case "ZS": return Mitling;
                        case "ZD": return Mitolin;
                        case "ZP": return Levir;
                        case "SF": return Ego;
                        case "SM": return Wife;
                        case "SB": return Son;
                        case "SZ": return Daughter;
                        case "SS": return GrandSon;
                        case "SD": return PaternalGranddaughter;
                        case "SP": return Schnerre;
                        case "DF": return Ego;
                        case "DM": return Ego;
                        case "DB": return Son;
                        case "DZ": return Daughter;
                        case "DS": return DaughterSon;
                        case "DD": return GrandDaughter;
                        case "DP": return Yerno;
                        case "PF": return Sweger;
                        case "PM": return Swegra;
                        case "PB": return Levir;
                        case "PZ": return Jeneter;
                        case "PS": return StepSon;
                        case "PD": return StepDaughter;
                        case "PP": return Jeneter;
                        default: return Error;
                    }
                case 3:
                    switch (RelationshipString)
                    {
                        case "FFF": return nthGrandFather(3);
                        case "FFM": return nthNanna(3);
                        case "FFB": return GreatFaedro(2);
                        case "FFZ": return GreatAunt(2);
                        case "FFS": return HalfFaedero(2);
                        case "FFD": return HalfAunt(2);
                        case "FFP": return StepNanna(2);
                        case "FMF": return Grandcestor(3);
                        case "FMM": return Grandcestress(3);
                        case "FMB": return GreatAunt(2);
                        case "FMZ": return GrandModrie(2);
                        case "FMS": return GreatUncle(2);
                        case "FMD": return GreatAunt(2);
                        case "FMP": return GreatGalla(2);
                        case "FBF": return GrandFather;
                        case "FBM": return Nanna;
                        case "FBB": return Faedro;
                        case "FBZ": return Aunt;
                        case "FBS": return AgnaticParallelCousin;
                        case "FBD": return AgnaticParallelCousinf;
                        case "FBP": return Gallen;
                        case "FZF": return GrandFather;
                        case "FZM": return Nanna;
                        case "FZB": return Faedro;
                        case "FZZ": return Aunt;
                        case "FZS": return CousinM(1);
                        case "FZD": return CousinF(1);
                        case "FZP": return Eame;
                        case "FSF": return Father;
                        case "FSM": return StepMother;
                        case "FSB": return Brother;
                        case "FSZ": return Sister;
                        case "FSS": return HalfNephew;
                        case "FSD": return HalfNiece;
                        case "FSP": return Jeneter;
                        case "FDF": return Father;
                        case "FDM": return StepMother;
                        case "FDB": return AgnaticBrother;
                        case "FDZ": return AgnaticSister;
                        case "FDS": return AlinealNephew(true, 1);
                        case "FDD": return UterineNiece(true, 1);
                        case "FDP": return Levir;
                        case "FPF": return StepMothersFather;
                        case "FPM": return StepMothersMother;
                        case "FPB": return Eame;
                        case "FPZ": return Gallen;
                        case "FPS": return StepBrother;
                        case "FPD": return StepSister;
                        case "FPP": return Error;
                        case "MFF": return Grandcestor(3);
                        case "MFM": return Grandcestress(3);
                        case "MFB": return GreatUncle(2);
                        case "MFZ": return GreatAunt(2);
                        case "MFS": return MothersAgnaticBrother;
                        case "MFD": return MothersAgnaticSister;
                        case "MFP": return StepGrandMother;
                        case "MMF": return Ancestor(RelationshipString);
                        case "MMM": return Ancestor(RelationshipString);
                        case "MMB": return GreatUncle(2);
                        case "MMZ": return GreatModrie(2);
                        case "MMS": return GreatUncle(2);
                        case "MMD": return HalfModrie;
                        case "MMP": return StepGrandFather;
                        case "MBF": return GetRelationship("MF");
                        case "MBM": return GetRelationship("");
                        case "MBB": return GetRelationship("MB");
                        case "MBZ": return GetRelationship("MZ");
                        case "MBS": throw new NotImplementedException();
                        case "MBD": throw new NotImplementedException();
                        case "MBP": return Gallen;
                        case "MZF": return GetRelationship("");
                        case "MZM": return GetRelationship("");
                        case "MZB": return GetRelationship("MB");
                        case "MZZ": throw new NotImplementedException();
                        case "MZS": throw new NotImplementedException();
                        case "MZD": throw new NotImplementedException();
                        case "MZP": return Eame;
                        case "MSF": throw new NotImplementedException();
                        case "MSM": throw new NotImplementedException();
                        case "MSB": return GetRelationship("");
                        case "MSZ": return GetRelationship("");
                        case "MSS": throw new NotImplementedException();
                        case "MSD": throw new NotImplementedException();
                        case "MSP": throw new NotImplementedException();
                        case "MDF": throw new NotImplementedException();
                        case "MDM": throw new NotImplementedException();
                        case "MDB": return GetRelationship("");
                        case "MDZ": return GetRelationship("");
                        case "MDS": return StepBrother;
                        case "MDD": throw new NotImplementedException();
                        case "MDP": throw new NotImplementedException();
                        case "MPF": throw new NotImplementedException();
                        case "MPM": throw new NotImplementedException();
                        case "MPB": throw new NotImplementedException();
                        case "MPZ": throw new NotImplementedException();
                        case "MPS": throw new NotImplementedException();
                        case "MPD": throw new NotImplementedException();
                        case "MPP": throw new NotImplementedException();
                        case "BFF": return GetRelationship("");
                        case "BFM": return GetRelationship("");
                        case "BFB": return GetRelationship("");
                        case "BFZ": return GetRelationship("");
                        case "BFS": return GetRelationship("");
                        case "BFD": return GetRelationship("");
                        case "BFP": return GetRelationship("");
                        case "BMF": return GetRelationship("");
                        case "BMM": return GetRelationship("");
                        case "BMB": return GetRelationship("");
                        case "BMZ": return GetRelationship("");
                        case "BMS": return GetRelationship("");
                        case "BMD": return GetRelationship("");
                        case "BMP": return GetRelationship("");
                        case "BBF": return Father;
                        case "BBM": return Mother;
                        case "BBB": return Brother;
                        case "BBZ": return Sister;
                        case "BBS": return Nephew;
                        case "BBD": return Niece;
                        case "BBP": return Jeneter;
                        case "BZF": return GetRelationship("ZF");
                        case "BZM": return GetRelationship("ZM");
                        case "BZB": return GetRelationship("ZB");
                        case "BZZ": return GetRelationship("ZZ");
                        case "BZS": return GetRelationship("ZS");
                        case "BZD": return GetRelationship("ZD");
                        case "BZP": return GetRelationship("ZP");
                        case "BSF": return Brother;
                        case "BSM": return Jeneter;
                        case "BSB": return GetRelationship("");
                        case "BSZ": return GetRelationship("");
                        case "BSS": return GreatNephew(2);
                        case "BSD": return BrotherSonDaughter;
                        case "BSP": return Schnerre(1, 1);
                        case "BDF": throw new NotImplementedException();
                        case "BDM": throw new NotImplementedException();
                        case "BDB": return Nephew;
                        case "BDZ": return GetRelationship("");
                        case "BDS": throw new NotImplementedException();
                        case "BDD": throw new NotImplementedException();
                        case "BDP": throw new NotImplementedException();
                        case "BPF": throw new NotImplementedException();
                        case "BPM": throw new NotImplementedException();
                        case "BPB": throw new NotImplementedException();
                        case "BPZ": throw new NotImplementedException();
                        case "BPS": throw new NotImplementedException();
                        case "BPD": throw new NotImplementedException();
                        case "BPP": return Error;
                        case "ZFF": return GrandSweger(2);
                        case "ZFM": return GrandSwegra(2);
                        case "ZFB": return GetRelationship("");
                        case "ZFZ": return GetRelationship("");
                        case "ZFS": return GetRelationship("");
                        case "ZFD": return GetRelationship("");
                        case "ZFP": return GetRelationship("");
                        case "ZMF": return GetRelationship("");
                        case "ZMM": return GetRelationship("");
                        case "ZMB": return GetRelationship("");
                        case "ZMZ": return GetRelationship("");
                        case "ZMS": return GetRelationship("");
                        case "ZMD": return GetRelationship("");
                        case "ZMP": return GetRelationship("");
                        case "ZBF": return GetRelationship("BF");
                        case "ZBM": return GetRelationship("BM");
                        case "ZBB": return Brother;
                        case "ZBZ": return Sister;
                        case "ZBS": return Nephew;
                        case "ZBD": return GetRelationship("BD");
                        case "ZBP": return GetRelationship("BP");
                        case "ZZF": return GetRelationship("ZF");
                        case "ZZM": return GetRelationship("ZM");
                        case "ZZB": return GetRelationship("ZB");
                        case "ZZZ": return GetRelationship("ZZ");
                        case "ZZS": return GetRelationship("ZS");
                        case "ZZD": return GetRelationship("ZD");
                        case "ZZP": return GetRelationship("ZP");
                        case "ZSF": throw new NotImplementedException();
                        case "ZSM": throw new NotImplementedException();
                        case "ZSB": return GetRelationship("");
                        case "ZSZ": return GetRelationship("");
                        case "ZSS": throw new NotImplementedException();
                        case "ZSD": throw new NotImplementedException();
                        case "ZSP": throw new NotImplementedException();
                        case "ZDF": throw new NotImplementedException();
                        case "ZDM": throw new NotImplementedException();
                        case "ZDB": return GetRelationship("");
                        case "ZDZ": return GetRelationship("");
                        case "ZDS": throw new NotImplementedException();
                        case "ZDD": throw new NotImplementedException();
                        case "ZDP": throw new NotImplementedException();
                        case "ZPF": throw new NotImplementedException();
                        case "ZPM": throw new NotImplementedException();
                        case "ZPB": throw new NotImplementedException();
                        case "ZPZ": throw new NotImplementedException();
                        case "ZPS": throw new NotImplementedException();
                        case "ZPD": throw new NotImplementedException();
                        case "ZPP": throw new NotImplementedException();
                        case "SFF": throw new NotImplementedException();
                        case "SFM": throw new NotImplementedException();
                        case "SFB": throw new NotImplementedException();
                        case "SFZ": throw new NotImplementedException();
                        case "SFS": throw new NotImplementedException();
                        case "SFD": throw new NotImplementedException();
                        case "SFP": throw new NotImplementedException();
                        case "SMF": throw new NotImplementedException();
                        case "SMM": throw new NotImplementedException();
                        case "SMB": throw new NotImplementedException();
                        case "SMZ": throw new NotImplementedException();
                        case "SMS": throw new NotImplementedException();
                        case "SMD": throw new NotImplementedException();
                        case "SMP": throw new NotImplementedException();
                        case "SBF": return GetRelationship("");
                        case "SBM": return GetRelationship("");
                        case "SBB": return Son;
                        case "SBZ": return GetRelationship("SZ");
                        case "SBS": return GetRelationship("");
                        case "SBD": return GetRelationship("");
                        case "SBP": return GetRelationship("");
                        case "SZF": return GetRelationship("");
                        case "SZM": return GetRelationship("");
                        case "SZB": return GetRelationship("SB");
                        case "SZZ": return GetRelationship("SZ");
                        case "SZS": return GetRelationship("");
                        case "SZD": return GetRelationship("");
                        case "SZP": return GetRelationship("");
                        case "SSF": throw new NotImplementedException();
                        case "SSM": throw new NotImplementedException();
                        case "SSB": return GetRelationship("");
                        case "SSZ": return GetRelationship("");
                        case "SSS": throw new NotImplementedException();
                        case "SSD": throw new NotImplementedException();
                        case "SSP": throw new NotImplementedException();
                        case "SDF": throw new NotImplementedException();
                        case "SDM": throw new NotImplementedException();
                        case "SDB": return GetRelationship("");
                        case "SDZ": return GetRelationship("");
                        case "SDS": throw new NotImplementedException();
                        case "SDD": throw new NotImplementedException();
                        case "SDP": throw new NotImplementedException();
                        case "SPF": return Macheton;
                        case "SPM": return Machetonie;
                        case "SPB": throw new NotImplementedException();
                        case "SPZ": throw new NotImplementedException();
                        case "SPS": throw new NotImplementedException();
                        case "SPD": throw new NotImplementedException();
                        case "SPP": throw new NotImplementedException();
                        case "DFF": throw new NotImplementedException();
                        case "DFM": throw new NotImplementedException();
                        case "DFB": throw new NotImplementedException();
                        case "DFZ": throw new NotImplementedException();
                        case "DFS": throw new NotImplementedException();
                        case "DFD": throw new NotImplementedException();
                        case "DFP": throw new NotImplementedException();
                        case "DMF": throw new NotImplementedException();
                        case "DMM": throw new NotImplementedException();
                        case "DMB": throw new NotImplementedException();
                        case "DMZ": throw new NotImplementedException();
                        case "DMS": throw new NotImplementedException();
                        case "DMD": throw new NotImplementedException();
                        case "DMP": throw new NotImplementedException();
                        case "DBF": return GetRelationship("");
                        case "DBM": return GetRelationship("");
                        case "DBB": return Son;
                        case "DBZ": return GetRelationship("DZ");
                        case "DBS": return GetRelationship("");
                        case "DBD": return GetRelationship("");
                        case "DBP": return GetRelationship("");
                        case "DZF": return GetRelationship("");
                        case "DZM": return GetRelationship("");
                        case "DZB": return GetRelationship("DB");
                        case "DZZ": return GetRelationship("DZ");
                        case "DZS": return GetRelationship("");
                        case "DZD": return GetRelationship("");
                        case "DZP": return GetRelationship("");
                        case "DSF": throw new NotImplementedException();
                        case "DSM": throw new NotImplementedException();
                        case "DSB": return GetRelationship("");
                        case "DSZ": return GetRelationship("");
                        case "DSS": throw new NotImplementedException();
                        case "DSD": throw new NotImplementedException();
                        case "DSP": throw new NotImplementedException();
                        case "DDF": throw new NotImplementedException();
                        case "DDM": throw new NotImplementedException();
                        case "DDB": return GetRelationship("");
                        case "DDZ": return GetRelationship("");
                        case "DDS": throw new NotImplementedException();
                        case "DDD": throw new NotImplementedException();
                        case "DDP": throw new NotImplementedException();
                        case "DPF": return Macheton;
                        case "DPM": return Machetonie;
                        case "DPB": throw new NotImplementedException();
                        case "DPZ": throw new NotImplementedException();
                        case "DPS": throw new NotImplementedException();
                        case "DPD": throw new NotImplementedException();
                        case "DPP": throw new NotImplementedException();
                        case "PFF": throw new NotImplementedException();
                        case "PFM": throw new NotImplementedException();
                        case "PFB": throw new NotImplementedException();
                        case "PFZ": throw new NotImplementedException();
                        case "PFS": throw new NotImplementedException();
                        case "PFD": throw new NotImplementedException();
                        case "PFP": throw new NotImplementedException();
                        case "PMF": throw new NotImplementedException();
                        case "PMM": throw new NotImplementedException();
                        case "PMB": throw new NotImplementedException();
                        case "PMZ": throw new NotImplementedException();
                        case "PMS": throw new NotImplementedException();
                        case "PMD": throw new NotImplementedException();
                        case "PMP": throw new NotImplementedException();
                        case "PBF": return GetRelationship("");
                        case "PBM": return GetRelationship("");
                        case "PBB": return Levir;
                        case "PBZ": return GetRelationship("PZ");
                        case "PBS": throw new NotImplementedException();
                        case "PBD": throw new NotImplementedException();
                        case "PBP": throw new NotImplementedException();
                        case "PZF": return GetRelationship("");
                        case "PZM": return GetRelationship("");
                        case "PZB": return GetRelationship("PB");
                        case "PZZ": return GetRelationship("PZ");
                        case "PZS": throw new NotImplementedException();
                        case "PZD": throw new NotImplementedException();
                        case "PZP": throw new NotImplementedException();
                        case "PSF": throw new NotImplementedException();
                        case "PSM": throw new NotImplementedException();
                        case "PSB": return GetRelationship("");
                        case "PSZ": return GetRelationship("");
                        case "PSS": throw new NotImplementedException();
                        case "PSD": throw new NotImplementedException();
                        case "PSP": throw new NotImplementedException();
                        case "PDF": throw new NotImplementedException();
                        case "PDM": throw new NotImplementedException();
                        case "PDB": return GetRelationship("");
                        case "PDZ": return GetRelationship("");
                        case "PDS": throw new NotImplementedException();
                        case "PDD": return StepGrandDaughter;
                        case "PDP": return StepYerno;
                        case "PPF": return Error;
                        case "PPM": return Error;
                        case "PPB": return Error;
                        case "PPZ": return Error;
                        case "PPS": return Error;
                        case "PPD": return Error;
                        case "PPP": return Error;
                        default: return Error;
                    }
                default:
                    throw new NotImplementedException();
            }
        }

        public string YourTitleFromConsanguinity(int YourGenerationsFromCommonAncestor, int TheirGenerationsFromCommonAncestor, bool half, char YourSex)
        {
            return YourTitleFromConsanguinity(YourGenerationsFromCommonAncestor, TheirGenerationsFromCommonAncestor, half, 'X', YourSex);
        }

        public string YourTitleFromConsanguinity(int YourGenerationsFromCommonAncestor, int TheirGenerationsFromCommonAncestor, bool half, char UterineOrY, char YourSex)
        {
            int diff = YourGenerationsFromCommonAncestor - TheirGenerationsFromCommonAncestor;
            int g = YourGenerationsFromCommonAncestor;
            if (TheirGenerationsFromCommonAncestor == 0)
            {
                return GetDescendantTitle(g, UterineOrY, YourSex);
            }
        }

        private string GetDescendantTitle(int GenerationsFromYou, char uterineOrY, char yourSex)
        {
            int g = GenerationsFromYou;
            switch (uterineOrY)
            {
                case 'U':
                case 'Y':
                default:
                    if (g = 1)
                    {

                    }
            }
        }

        private string GrandSwegra(int v)
        {
            throw new NotImplementedException();
        }

        private string Schnerre(int v1, int v2)
        {
            throw new NotImplementedException();
        }

        private string GreatNephew(int v)
        {
            throw new NotImplementedException();
        }

        private string GreatModrie(int v)
        {
            throw new NotImplementedException();
        }

        private string GrandSweger(int v)
        {
            throw new NotImplementedException();
        }

        private string Ancestor(string relationshipString)
        {
            throw new NotImplementedException();
        }

        private string UterineNiece(bool v1, int v2)
        {
            throw new NotImplementedException();
        }

        private string AlinealNephew(bool v1, int v2)
        {
            throw new NotImplementedException();
        }

        private string CousinF(int v)
        {
            throw new NotImplementedException();
        }

        private string CousinM(int v)
        {
            throw new NotImplementedException();
        }

        private string GreatGalla(int v)
        {
            throw new NotImplementedException();
        }

        private string GreatUncle(int v)
        {
            throw new NotImplementedException();
        }

        private string GrandModrie(int v)
        {
            throw new NotImplementedException();
        }

        private string Grandcestress(int v)
        {
            throw new NotImplementedException();
        }

        private string Grandcestor(int v)
        {
            throw new NotImplementedException();
        }

        private string StepNanna(int v)
        {
            throw new NotImplementedException();
        }

        private string HalfAunt(int v)
        {
            throw new NotImplementedException();
        }

        private string HalfFaedero(int v)
        {
            throw new NotImplementedException();
        }

        private string GreatAunt(int v)
        {
            throw new NotImplementedException();
        }

        private string GreatFaedro(int v)
        {
            throw new NotImplementedException();
        }

        private string nthNanna(int v)
        {
            throw new NotImplementedException();
        }

        private string nthGrandFather(int v)
        {
            throw new NotImplementedException();
        }
    }
}