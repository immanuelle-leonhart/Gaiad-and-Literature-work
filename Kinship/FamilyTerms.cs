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
                        case "MFP": return NotImplemented;
                        case "MMF": return Ancestor(RelationshipString);
                        case "MMM": return Ancestor(RelationshipString);
                        case "MMB": return NotImplemented;
                        case "MMZ": return GreatModrie(2);
                        case "MMS": return GreatUncle(2);
                        case "MMD": return NotImplemented;
                        case "MMP": return NotImplemented;
                        case "MBF": return NotImplemented;
                        case "MBM": return NotImplemented;
                        case "MBB": return GetRelationship("MB");
                        case "MBZ": return GetRelationship("MZ");
                        case "MBS": return NotImplemented;
                        case "MBD": return NotImplemented;
                        case "MBP": return Gallen;
                        case "MZF": return NotImplemented;
                        case "MZM": return NotImplemented;
                        case "MZB": return GetRelationship("MB");
                        case "MZZ": return NotImplemented;
                        case "MZS": return NotImplemented;
                        case "MZD": return NotImplemented;
                        case "MZP": return Eame;
                        case "MSF": return NotImplemented;
                        case "MSM": return NotImplemented;
                        case "MSB": return GetRelationship("");
                        case "MSZ": return GetRelationship("");
                        case "MSS": return NotImplemented;
                        case "MSD": return NotImplemented;
                        case "MSP": return NotImplemented;
                        case "MDF": return NotImplemented;
                        case "MDM": return NotImplemented;
                        case "MDB": return GetRelationship("");
                        case "MDZ": return GetRelationship("");
                        case "MDS": return NotImplemented;
                        case "MDD": return NotImplemented;
                        case "MDP": return NotImplemented;
                        case "MPF": return NotImplemented;
                        case "MPM": return NotImplemented;
                        case "MPB": return NotImplemented;
                        case "MPZ": return NotImplemented;
                        case "MPS": return NotImplemented;
                        case "MPD": return NotImplemented;
                        case "MPP": return NotImplemented;
                        case "BFF": return NotImplemented;
                        case "BFM": return NotImplemented;
                        case "BFB": return NotImplemented;
                        case "BFZ": return NotImplemented;
                        case "BFS": return NotImplemented;
                        case "BFD": return NotImplemented;
                        case "BFP": return NotImplemented;
                        case "BMF": return NotImplemented;
                        case "BMM": return NotImplemented;
                        case "BMB": return NotImplemented;
                        case "BMZ": return NotImplemented;
                        case "BMS": return NotImplemented;
                        case "BMD": return NotImplemented;
                        case "BMP": return NotImplemented;
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
                        case "BSF": return NotImplemented;
                        case "BSM": return NotImplemented;
                        case "BSB": return GetRelationship("");
                        case "BSZ": return GetRelationship("");
                        case "BSS": return NotImplemented;
                        case "BSD": return NotImplemented;
                        case "BSP": return NotImplemented;
                        case "BDF": return NotImplemented;
                        case "BDM": return NotImplemented;
                        case "BDB": return Nephew;
                        case "BDZ": return GetRelationship("");
                        case "BDS": return NotImplemented;
                        case "BDD": return NotImplemented;
                        case "BDP": return NotImplemented;
                        case "BPF": return NotImplemented;
                        case "BPM": return NotImplemented;
                        case "BPB": return NotImplemented;
                        case "BPZ": return NotImplemented;
                        case "BPS": return NotImplemented;
                        case "BPD": return NotImplemented;
                        case "BPP": return Error;
                        case "ZFF": return GrandSweger(2);
                        case "ZFM": return GrandSwegra(2);
                        case "ZFB": return NotImplemented;
                        case "ZFZ": return NotImplemented;
                        case "ZFS": return NotImplemented;
                        case "ZFD": return NotImplemented;
                        case "ZFP": return NotImplemented;
                        case "ZMF": return NotImplemented;
                        case "ZMM": return NotImplemented;
                        case "ZMB": return NotImplemented;
                        case "ZMZ": return NotImplemented;
                        case "ZMS": return NotImplemented;
                        case "ZMD": return NotImplemented;
                        case "ZMP": return NotImplemented;
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
                        case "ZSF": return NotImplemented;
                        case "ZSM": return NotImplemented;
                        case "ZSB": return GetRelationship("");
                        case "ZSZ": return GetRelationship("");
                        case "ZSS": return NotImplemented;
                        case "ZSD": return NotImplemented;
                        case "ZSP": return NotImplemented;
                        case "ZDF": return NotImplemented;
                        case "ZDM": return NotImplemented;
                        case "ZDB": return GetRelationship("");
                        case "ZDZ": return GetRelationship("");
                        case "ZDS": return NotImplemented;
                        case "ZDD": return NotImplemented;
                        case "ZDP": return NotImplemented;
                        case "ZPF": return NotImplemented;
                        case "ZPM": return NotImplemented;
                        case "ZPB": return NotImplemented;
                        case "ZPZ": return NotImplemented;
                        case "ZPS": return NotImplemented;
                        case "ZPD": return NotImplemented;
                        case "ZPP": return NotImplemented;
                        case "SFF": return NotImplemented;
                        case "SFM": return NotImplemented;
                        case "SFB": return NotImplemented;
                        case "SFZ": return NotImplemented;
                        case "SFS": return NotImplemented;
                        case "SFD": return NotImplemented;
                        case "SFP": return NotImplemented;
                        case "SMF": return NotImplemented;
                        case "SMM": return NotImplemented;
                        case "SMB": return NotImplemented;
                        case "SMZ": return NotImplemented;
                        case "SMS": return NotImplemented;
                        case "SMD": return NotImplemented;
                        case "SMP": return NotImplemented;
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
                        case "SSF": return NotImplemented;
                        case "SSM": return NotImplemented;
                        case "SSB": return GetRelationship("");
                        case "SSZ": return GetRelationship("");
                        case "SSS": return NotImplemented;
                        case "SSD": return NotImplemented;
                        case "SSP": return NotImplemented;
                        case "SDF": return NotImplemented;
                        case "SDM": return NotImplemented;
                        case "SDB": return GetRelationship("");
                        case "SDZ": return GetRelationship("");
                        case "SDS": return NotImplemented;
                        case "SDD": return NotImplemented;
                        case "SDP": return NotImplemented;
                        case "SPF": return Macheton;
                        case "SPM": return Machetonie;
                        case "SPB": return NotImplemented;
                        case "SPZ": return NotImplemented;
                        case "SPS": return NotImplemented;
                        case "SPD": return NotImplemented;
                        case "SPP": return NotImplemented;
                        case "DFF": return NotImplemented;
                        case "DFM": return NotImplemented;
                        case "DFB": return NotImplemented;
                        case "DFZ": return NotImplemented;
                        case "DFS": return NotImplemented;
                        case "DFD": return NotImplemented;
                        case "DFP": return NotImplemented;
                        case "DMF": return NotImplemented;
                        case "DMM": return NotImplemented;
                        case "DMB": return NotImplemented;
                        case "DMZ": return NotImplemented;
                        case "DMS": return NotImplemented;
                        case "DMD": return NotImplemented;
                        case "DMP": return NotImplemented;
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
                        case "DSF": return NotImplemented;
                        case "DSM": return NotImplemented;
                        case "DSB": return GetRelationship("");
                        case "DSZ": return GetRelationship("");
                        case "DSS": return NotImplemented;
                        case "DSD": return NotImplemented;
                        case "DSP": return NotImplemented;
                        case "DDF": return NotImplemented;
                        case "DDM": return NotImplemented;
                        case "DDB": return GetRelationship("");
                        case "DDZ": return GetRelationship("");
                        case "DDS": return NotImplemented;
                        case "DDD": return NotImplemented;
                        case "DDP": return NotImplemented;
                        case "DPF": return Macheton;
                        case "DPM": return Machetonie;
                        case "DPB": return NotImplemented;
                        case "DPZ": return NotImplemented;
                        case "DPS": return NotImplemented;
                        case "DPD": return NotImplemented;
                        case "DPP": return NotImplemented;
                        case "PFF": return NotImplemented;
                        case "PFM": return NotImplemented;
                        case "PFB": return NotImplemented;
                        case "PFZ": return NotImplemented;
                        case "PFS": return NotImplemented;
                        case "PFD": return NotImplemented;
                        case "PFP": return NotImplemented;
                        case "PMF": return NotImplemented;
                        case "PMM": return NotImplemented;
                        case "PMB": return NotImplemented;
                        case "PMZ": return NotImplemented;
                        case "PMS": return NotImplemented;
                        case "PMD": return NotImplemented;
                        case "PMP": return NotImplemented;
                        case "PBF": return NotImplemented;
                        case "PBM": return NotImplemented;
                        case "PBB": return Levir;
                        case "PBZ": return GetRelationship("PZ");
                        case "PBS": return NotImplemented;
                        case "PBD": return NotImplemented;
                        case "PBP": return NotImplemented;
                        case "PZF": return NotImplemented;
                        case "PZM": return NotImplemented;
                        case "PZB": return GetRelationship("PB");
                        case "PZZ": return GetRelationship("PZ");
                        case "PZS": return NotImplemented;
                        case "PZD": return NotImplemented;
                        case "PZP": return NotImplemented;
                        case "PSF": return NotImplemented;
                        case "PSM": return NotImplemented;
                        case "PSB": return GetRelationship("");
                        case "PSZ": return GetRelationship("");
                        case "PSS": return NotImplemented;
                        case "PSD": return NotImplemented;
                        case "PSP": return NotImplemented;
                        case "PDF": return NotImplemented;
                        case "PDM": return NotImplemented;
                        case "PDB": return GetRelationship("");
                        case "PDZ": return GetRelationship("");
                        case "PDS": return NotImplemented;
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