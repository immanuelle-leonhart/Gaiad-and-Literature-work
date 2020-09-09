using System;
using System.IO;

namespace Kinship
{
    public class FamilyTerms
    {
        public string Ego { get; private set; }
        public string Father { get; private set; }
        public string Mother { get; private set; }
        public string Son { get; private set; }
        public string Daughter { get; private set; }
        public string Partner { get; private set; }
        public string Error { get; private set; }
        public string Brother { get; private set; }
        public string Sister { get; private set; }
        public string GrandFather { get; private set; }
        public string Nanna { get; private set; }
        public string AgnaticBrother { get; private set; }
        public string AgnaticSister { get; private set; }
        public string StepMother { get; private set; }
        public string GenGen { get; private set; }
        public string GrandMother { get; private set; }
        public string UterineBrother { get; private set; }
        public string UterineSister { get; private set; }
        public string StepFather { get; private set; }
        public string PaternalGrandson { get; private set; }
        public string PaternalGranddaughter { get; private set; }
        public string Schnerre { get; private set; }
        public string MaternalGrandson { get; private set; }
        public string MaternalGranddaughter { get; private set; }
        public string Yerno { get; private set; }
        public string Sweger { get; private set; }
        public string Swegra { get; private set; }
        public string StepSon { get; private set; }
        public string StepDaughter { get; private set; }

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
                        case "BS":
                            return Brother;
                        case "BD":
                            return Sister;
                        case "FF":
                            return GrandFather;
                        case "FM":
                            return Nanna;
                        case "FS":
                            return AgnaticBrother;
                        case "FD":
                            return AgnaticSister;
                        case "FP":
                            return StepMother;
                        case "MF":
                            return GenGen;
                        case "MM":
                            return GrandMother;
                        case "MS":
                            return UterineBrother;
                        case "MD":
                            return UterineSister;
                        case "MP":
                            return StepFather;
                        case "SS":
                            return PaternalGrandson;
                        case "SD":
                            return PaternalGranddaughter;
                        case "SP":
                            return Schnerre;
                        case "DS":
                            return MaternalGrandson;
                        case "DD":
                            return MaternalGranddaughter;
                        case "DP":
                            return Yerno;
                        case "PF":
                            return Sweger;
                        case "PM":
                            return Swegra;
                        case "PS":
                            return StepSon;
                        case "PD":
                            return StepDaughter;
                        default:
                            return Error;
                    }
                case 3:
                    switch (RelationshipString)
                    {
                        case "BSS":
                            return FraternalNephew;
                        case "BSD":
                            return FraternalNiece;
                        case "BSP":
                            return 
                        case "BDS":
                        case "BDD":
                        case "BDP":
                        case "FSS":
                        case "FSD":
                        case "FSP":
                        case "FDS":
                        case "FDD":
                        case "FDP":
                        case "MSS":
                        case "MSD":
                        case "MSP":
                        case "MDS":
                        case "MDD":
                        case "MDP":
                        case "FBS":
                        case "FBD":
                        case "FFF":
                        case "FFM":
                        case "FFS":
                        case "FFD":
                        case "FFP":
                        case "FMF":
                        case "FMM":
                        case "FMS":
                        case "FMD":
                        case "FMP":
                        case "MBS":
                        case "MBD":
                        case "MFF":
                        case "MFM":
                        case "MFS":
                        case "MFD":
                        case "MFP":
                        case "MMF":
                        case "MMM":
                        case "MMS":
                        case "MMD":
                        case "MMP":
                        case "SSS":
                            //return PaternalGrandson;
                        case "SSD":
                            //return PaternalGranddaughter;
                        case "SSP":
                            //return Schnerre;
                        case "SDS":
                            //return MaternalGrandson;
                        case "SDD":
                            //return MaternalGranddaughter;
                        case "SDP":
                            //return Yerno;
                        case "SPF":
                            //return Sweger;
                        case "SPM":
                            //return Swegra;
                        case "SPS":
                            //return StepSon;
                        case "SPD":
                            //return StepDaughter;
                        case "DSS":
                            //return PaternalGrandson;
                        case "DSD":
                            //return PaternalGranddaughter;
                        case "DSP":
                            //return Schnerre;
                        case "DDS":
                            //return MaternalGrandson;
                        case "DDD":
                            //return MaternalGranddaughter;
                        case "DDP":
                            //return Yerno;
                        case "DPF":
                            //return Sweger;
                        case "DPM":
                            //return Swegra;
                        case "DPS":
                            //return StepSon;
                        case "DPD":
                            //return StepDaughter;
                        default:
                            throw new NotImplementedException();
                    }
                default:
                    throw new NotImplementedException();
            }
        }
    }
}
