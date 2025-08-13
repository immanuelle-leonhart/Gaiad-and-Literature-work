using System;
using System.IO;

namespace Kinship
{
    public class Relative
    {
        public static Relative Ego { get; private set; }
        public static Relative Father { get; private set; }
        public static Relative Mother { get; private set; }
        public static Relative Brother { get; private set; }
        public static Relative Sister { get; private set; }
        public static Relative Son { get; private set; }
        public static Relative Daughter { get; private set; }
        public static Relative Partner { get; private set; }
        public static Relative GrandFather { get; private set; }
        public static Relative Nanna { get; private set; }
        public static Relative Faedro { get; private set; }
        public static Relative Aunt { get; private set; }
        public static Relative AgnaticBrother { get; private set; }
        public static Relative AgnaticSister { get; private set; }
        public static Relative StepMother { get; private set; }
        public static Relative GenGen { get; private set; }
        public static Relative GrandMother { get; private set; }
        public static Relative Uncle { get; private set; }
        public static Relative Modrie { get; private set; }
        public static Relative UterineBrother { get; private set; }
        public static Relative UterineSister { get; private set; }
        public static Relative StepFather { get; private set; }
        public static Relative PaternalNephew { get; private set; }
        public static Relative PaternalNiece { get; private set; }
        public static Relative Jeneter { get; private set; }
        public static Relative MaternalNephew { get; private set; }
        public static Relative MaternalNiece { get; private set; }
        public static Relative Levir { get; private set; }
        public static Relative Wife { get; private set; }
        public static Relative PaternalGrandSon { get; private set; }
        public static Relative PaternalGranddaughter { get; private set; }
        public static Relative Schnerre { get; private set; }
        public static Relative MaternalGrandson { get; private set; }
        public static Relative MaternalGrandDaughter { get; private set; }
        public static Relative Yerno { get; private set; }
        public static Relative Sweger { get; private set; }
        public static Relative Swegra { get; private set; }
        public static Relative StepSon { get; private set; }
        public static Relative StepDaughter { get; private set; }

        public static Relative GetRelationship(string RelationshipString)
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
                            return null;
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
                        case "BS": return PaternalNephew;
                        case "BD": return PaternalNiece;
                        case "BP": return Jeneter;
                        case "ZF": return Father;
                        case "ZM": return Mother;
                        case "ZB": return Brother;
                        case "ZZ": return Sister;
                        case "ZS": return MaternalNephew;
                        case "ZD": return MaternalNiece;
                        case "ZP": return Levir;
                        case "SF": return Ego;
                        case "SM": return Wife;
                        case "SB": return Son;
                        case "SZ": return Daughter;
                        case "SS": return PaternalGrandSon;
                        case "SD": return PaternalGranddaughter;
                        case "SP": return Schnerre;
                        case "DF": return Ego;
                        case "DM": return Ego;
                        case "DB": return Son;
                        case "DZ": return Daughter;
                        case "DS": return MaternalGrandson;
                        case "DD": return MaternalGrandDaughter;
                        case "DP": return Yerno;
                        case "PF": return Sweger;
                        case "PM": return Swegra;
                        case "PB": return Levir;
                        case "PZ": return Jeneter;
                        case "PS": return StepSon;
                        case "PD": return StepDaughter;
                        case "PP": return Jeneter;
                        default: return null;
                    }
                default:
                    return RelationshipAlgorithm(RelationshipString);
            }
        }

        public static Relative RelationshipAlgorithm(string relationshipString)
        {
            Clean(relationshipString);
            switch (relationshipString[0])
            {
                case 'F':
                case 'M':
                    return AncestralAlgorithm(relationshipString);
                case 'Z':
                case 'B':
                    return SiblingAlgorithm(relationshipString);
                case 'D':
                case 'S':
                    return DescendantAlgorithm(relationshipString);
                case 'P':
                    return InLawAlgorithm(relationshipString);
                default:
                    return null;
            }
        }

        private static Relative AncestralAlgorithm(string relationshipString)
        {
            throw new NotImplementedException();
        }

        private static Relative SiblingAlgorithm(string relationshipString)
        {
            throw new NotImplementedException();
        }

        private static Relative DescendantAlgorithm(string relationshipString)
        {
            throw new NotImplementedException();
        }

        private static Relative InLawAlgorithm(string relationshipString)
        {
            throw new NotImplementedException();
        }

        private static void Clean(string relationshipString)
        {
            while (relationshipString.Contains("PP") || relationshipString.Contains("ZZ") || relationshipString.Contains("BB") || relationshipString.Contains("BF") || relationshipString.Contains("ZF") || relationshipString.Contains("ZM") || relationshipString.Contains("BM") || relationshipString.Contains("SB") || relationshipString.Contains("SZ") || relationshipString.Contains("DB") || relationshipString.Contains("DZ"))
            {
                relationshipString.Replace("PP", "");
                relationshipString.Replace("ZZ", "Z");
                relationshipString.Replace("BB", "B");
                relationshipString.Replace("BF", "F");
                relationshipString.Replace("ZF", "F");
                relationshipString.Replace("ZM", "M");
                relationshipString.Replace("BM", "M");
                relationshipString.Replace("SB", "S");
                relationshipString.Replace("SZ", "D");
                relationshipString.Replace("DB", "S");
                relationshipString.Replace("DZ", "D");
            }
        }
    }
}