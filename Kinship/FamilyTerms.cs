using System;
using System.IO;

namespace Kinship
{
    public class FamilyTerms
    {
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
                            return PaternalGranddaughter
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
                default:
                    throw new NotImplementedException();
            }
        }
    }
}
