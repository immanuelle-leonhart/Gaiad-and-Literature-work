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
                        case "bbb": return Error; case "bbf": return Error; case "bbm": return Error; case "bbs": return Error; case "bbd": return Error; case "bfb": return Error; case "bff": return Error; case "bfm": return Error; case "bfs": return Error; case "bfd": return Error; case "bmb": return Error; case "bmf": return Error; case "bmm": return Error; case "bms": return Error; case "bmd": return Error; case "bsb": return Error; case "bsf": return Error; case "bsm": return Error; case "bss": return Error; case "bsd": return Error; case "bdb": return Error; case "bdf": return Error; case "bdm": return Error; case "bds": return Error; case "bdd": return Error; case "fbb": return Error; case "fbf": return Error; case "fbm": return Error; case "fbs": return Error; case "fbd": return Error; case "ffb": return Error; case "fff": return Error; case "ffm": return Error; case "ffs": return Error; case "ffd": return Error; case "fmb": return Error; case "fmf": return Error; case "fmm": return Error; case "fms": return Error; case "fmd": return Error; case "fsb": return Error; case "fsf": return Error; case "fsm": return Error; case "fss": return Error; case "fsd": return Error; case "fdb": return Error; case "fdf": return Error; case "fdm": return Error; case "fds": return Error; case "fdd": return Error; case "mbb": return Error; case "mbf": return Error; case "mbm": return Error; case "mbs": return Error; case "mbd": return Error; case "mfb": return Error; case "mff": return Error; case "mfm": return Error; case "mfs": return Error; case "mfd": return Error; case "mmb": return Error; case "mmf": return Error; case "mmm": return Error; case "mms": return Error; case "mmd": return Error; case "msb": return Error; case "msf": return Error; case "msm": return Error; case "mss": return Error; case "msd": return Error; case "mdb": return Error; case "mdf": return Error; case "mdm": return Error; case "mds": return Error; case "mdd": return Error; case "sbb": return Error; case "sbf": return Error; case "sbm": return Error; case "sbs": return Error; case "sbd": return Error; case "sfb": return Error; case "sff": return Error; case "sfm": return Error; case "sfs": return Error; case "sfd": return Error; case "smb": return Error; case "smf": return Error; case "smm": return Error; case "sms": return Error; case "smd": return Error; case "ssb": return Error; case "ssf": return Error; case "ssm": return Error; case "sss": return Error; case "ssd": return Error; case "sdb": return Error; case "sdf": return Error; case "sdm": return Error; case "sds": return Error; case "sdd": return Error; case "dbb": return Error; case "dbf": return Error; case "dbm": return Error; case "dbs": return Error; case "dbd": return Error; case "dfb": return Error; case "dff": return Error; case "dfm": return Error; case "dfs": return Error; case "dfd": return Error; case "dmb": return Error; case "dmf": return Error; case "dmm": return Error; case "dms": return Error; case "dmd": return Error; case "dsb": return Error; case "dsf": return Error; case "dsm": return Error; case "dss": return Error; case "dsd": return Error; case "ddb": return Error; case "ddf": return Error; case "ddm": return Error; case "dds": return Error; case "ddd": return Error;
                        default:
                            throw new NotImplementedException();
                    }
                case 4:
                    switch (RelationshipString)
                    {
                        case "bbbb": return Error; case "bbbf": return Error; case "bbbm": return Error; case "bbbs": return Error; case "bbbd": return Error; case "bbfb": return Error; case "bbff": return Error; case "bbfm": return Error; case "bbfs": return Error; case "bbfd": return Error; case "bbmb": return Error; case "bbmf": return Error; case "bbmm": return Error; case "bbms": return Error; case "bbmd": return Error; case "bbsb": return Error; case "bbsf": return Error; case "bbsm": return Error; case "bbss": return Error; case "bbsd": return Error; case "bbdb": return Error; case "bbdf": return Error; case "bbdm": return Error; case "bbds": return Error; case "bbdd": return Error; case "bfbb": return Error; case "bfbf": return Error; case "bfbm": return Error; case "bfbs": return Error; case "bfbd": return Error; case "bffb": return Error; case "bfff": return Error; case "bffm": return Error; case "bffs": return Error; case "bffd": return Error; case "bfmb": return Error; case "bfmf": return Error; case "bfmm": return Error; case "bfms": return Error; case "bfmd": return Error; case "bfsb": return Error; case "bfsf": return Error; case "bfsm": return Error; case "bfss": return Error; case "bfsd": return Error; case "bfdb": return Error; case "bfdf": return Error; case "bfdm": return Error; case "bfds": return Error; case "bfdd": return Error; case "bmbb": return Error; case "bmbf": return Error; case "bmbm": return Error; case "bmbs": return Error; case "bmbd": return Error; case "bmfb": return Error; case "bmff": return Error; case "bmfm": return Error; case "bmfs": return Error; case "bmfd": return Error; case "bmmb": return Error; case "bmmf": return Error; case "bmmm": return Error; case "bmms": return Error; case "bmmd": return Error; case "bmsb": return Error; case "bmsf": return Error; case "bmsm": return Error; case "bmss": return Error; case "bmsd": return Error; case "bmdb": return Error; case "bmdf": return Error; case "bmdm": return Error; case "bmds": return Error; case "bmdd": return Error; case "bsbb": return Error; case "bsbf": return Error; case "bsbm": return Error; case "bsbs": return Error; case "bsbd": return Error; case "bsfb": return Error; case "bsff": return Error; case "bsfm": return Error; case "bsfs": return Error; case "bsfd": return Error; case "bsmb": return Error; case "bsmf": return Error; case "bsmm": return Error; case "bsms": return Error; case "bsmd": return Error; case "bssb": return Error; case "bssf": return Error; case "bssm": return Error; case "bsss": return Error; case "bssd": return Error; case "bsdb": return Error; case "bsdf": return Error; case "bsdm": return Error; case "bsds": return Error; case "bsdd": return Error; case "bdbb": return Error; case "bdbf": return Error; case "bdbm": return Error; case "bdbs": return Error; case "bdbd": return Error; case "bdfb": return Error; case "bdff": return Error; case "bdfm": return Error; case "bdfs": return Error; case "bdfd": return Error; case "bdmb": return Error; case "bdmf": return Error; case "bdmm": return Error; case "bdms": return Error; case "bdmd": return Error; case "bdsb": return Error; case "bdsf": return Error; case "bdsm": return Error; case "bdss": return Error; case "bdsd": return Error; case "bddb": return Error; case "bddf": return Error; case "bddm": return Error; case "bdds": return Error; case "bddd": return Error; case "fbbb": return Error; case "fbbf": return Error; case "fbbm": return Error; case "fbbs": return Error; case "fbbd": return Error; case "fbfb": return Error; case "fbff": return Error; case "fbfm": return Error; case "fbfs": return Error; case "fbfd": return Error; case "fbmb": return Error; case "fbmf": return Error; case "fbmm": return Error; case "fbms": return Error; case "fbmd": return Error; case "fbsb": return Error; case "fbsf": return Error; case "fbsm": return Error; case "fbss": return Error; case "fbsd": return Error; case "fbdb": return Error; case "fbdf": return Error; case "fbdm": return Error; case "fbds": return Error; case "fbdd": return Error; case "ffbb": return Error; case "ffbf": return Error; case "ffbm": return Error; case "ffbs": return Error; case "ffbd": return Error; case "fffb": return Error; case "ffff": return Error; case "fffm": return Error; case "fffs": return Error; case "fffd": return Error; case "ffmb": return Error; case "ffmf": return Error; case "ffmm": return Error; case "ffms": return Error; case "ffmd": return Error; case "ffsb": return Error; case "ffsf": return Error; case "ffsm": return Error; case "ffss": return Error; case "ffsd": return Error; case "ffdb": return Error; case "ffdf": return Error; case "ffdm": return Error; case "ffds": return Error; case "ffdd": return Error; case "fmbb": return Error; case "fmbf": return Error; case "fmbm": return Error; case "fmbs": return Error; case "fmbd": return Error; case "fmfb": return Error; case "fmff": return Error; case "fmfm": return Error; case "fmfs": return Error; case "fmfd": return Error; case "fmmb": return Error; case "fmmf": return Error; case "fmmm": return Error; case "fmms": return Error; case "fmmd": return Error; case "fmsb": return Error; case "fmsf": return Error; case "fmsm": return Error; case "fmss": return Error; case "fmsd": return Error; case "fmdb": return Error; case "fmdf": return Error; case "fmdm": return Error; case "fmds": return Error; case "fmdd": return Error; case "fsbb": return Error; case "fsbf": return Error; case "fsbm": return Error; case "fsbs": return Error; case "fsbd": return Error; case "fsfb": return Error; case "fsff": return Error; case "fsfm": return Error; case "fsfs": return Error; case "fsfd": return Error; case "fsmb": return Error; case "fsmf": return Error; case "fsmm": return Error; case "fsms": return Error; case "fsmd": return Error; case "fssb": return Error; case "fssf": return Error; case "fssm": return Error; case "fsss": return Error; case "fssd": return Error; case "fsdb": return Error; case "fsdf": return Error; case "fsdm": return Error; case "fsds": return Error; case "fsdd": return Error; case "fdbb": return Error; case "fdbf": return Error; case "fdbm": return Error; case "fdbs": return Error; case "fdbd": return Error; case "fdfb": return Error; case "fdff": return Error; case "fdfm": return Error; case "fdfs": return Error; case "fdfd": return Error; case "fdmb": return Error; case "fdmf": return Error; case "fdmm": return Error; case "fdms": return Error; case "fdmd": return Error; case "fdsb": return Error; case "fdsf": return Error; case "fdsm": return Error; case "fdss": return Error; case "fdsd": return Error; case "fddb": return Error; case "fddf": return Error; case "fddm": return Error; case "fdds": return Error; case "fddd": return Error; case "mbbb": return Error; case "mbbf": return Error; case "mbbm": return Error; case "mbbs": return Error; case "mbbd": return Error; case "mbfb": return Error; case "mbff": return Error; case "mbfm": return Error; case "mbfs": return Error; case "mbfd": return Error; case "mbmb": return Error; case "mbmf": return Error; case "mbmm": return Error; case "mbms": return Error; case "mbmd": return Error; case "mbsb": return Error; case "mbsf": return Error; case "mbsm": return Error; case "mbss": return Error; case "mbsd": return Error; case "mbdb": return Error; case "mbdf": return Error; case "mbdm": return Error; case "mbds": return Error; case "mbdd": return Error; case "mfbb": return Error; case "mfbf": return Error; case "mfbm": return Error; case "mfbs": return Error; case "mfbd": return Error; case "mffb": return Error; case "mfff": return Error; case "mffm": return Error; case "mffs": return Error; case "mffd": return Error; case "mfmb": return Error; case "mfmf": return Error; case "mfmm": return Error; case "mfms": return Error; case "mfmd": return Error; case "mfsb": return Error; case "mfsf": return Error; case "mfsm": return Error; case "mfss": return Error; case "mfsd": return Error; case "mfdb": return Error; case "mfdf": return Error; case "mfdm": return Error; case "mfds": return Error; case "mfdd": return Error; case "mmbb": return Error; case "mmbf": return Error; case "mmbm": return Error; case "mmbs": return Error; case "mmbd": return Error; case "mmfb": return Error; case "mmff": return Error; case "mmfm": return Error; case "mmfs": return Error; case "mmfd": return Error; case "mmmb": return Error; case "mmmf": return Error; case "mmmm": return Error; case "mmms": return Error; case "mmmd": return Error; case "mmsb": return Error; case "mmsf": return Error; case "mmsm": return Error; case "mmss": return Error; case "mmsd": return Error; case "mmdb": return Error; case "mmdf": return Error; case "mmdm": return Error; case "mmds": return Error; case "mmdd": return Error; case "msbb": return Error; case "msbf": return Error; case "msbm": return Error; case "msbs": return Error; case "msbd": return Error; case "msfb": return Error; case "msff": return Error; case "msfm": return Error; case "msfs": return Error; case "msfd": return Error; case "msmb": return Error; case "msmf": return Error; case "msmm": return Error; case "msms": return Error; case "msmd": return Error; case "mssb": return Error; case "mssf": return Error; case "mssm": return Error; case "msss": return Error; case "mssd": return Error; case "msdb": return Error; case "msdf": return Error; case "msdm": return Error; case "msds": return Error; case "msdd": return Error; case "mdbb": return Error; case "mdbf": return Error; case "mdbm": return Error; case "mdbs": return Error; case "mdbd": return Error; case "mdfb": return Error; case "mdff": return Error; case "mdfm": return Error; case "mdfs": return Error; case "mdfd": return Error; case "mdmb": return Error; case "mdmf": return Error; case "mdmm": return Error; case "mdms": return Error; case "mdmd": return Error; case "mdsb": return Error; case "mdsf": return Error; case "mdsm": return Error; case "mdss": return Error; case "mdsd": return Error; case "mddb": return Error; case "mddf": return Error; case "mddm": return Error; case "mdds": return Error; case "mddd": return Error; case "sbbb": return Error; case "sbbf": return Error; case "sbbm": return Error; case "sbbs": return Error; case "sbbd": return Error; case "sbfb": return Error; case "sbff": return Error; case "sbfm": return Error; case "sbfs": return Error; case "sbfd": return Error; case "sbmb": return Error; case "sbmf": return Error; case "sbmm": return Error; case "sbms": return Error; case "sbmd": return Error; case "sbsb": return Error; case "sbsf": return Error; case "sbsm": return Error; case "sbss": return Error; case "sbsd": return Error; case "sbdb": return Error; case "sbdf": return Error; case "sbdm": return Error; case "sbds": return Error; case "sbdd": return Error; case "sfbb": return Error; case "sfbf": return Error; case "sfbm": return Error; case "sfbs": return Error; case "sfbd": return Error; case "sffb": return Error; case "sfff": return Error; case "sffm": return Error; case "sffs": return Error; case "sffd": return Error; case "sfmb": return Error; case "sfmf": return Error; case "sfmm": return Error; case "sfms": return Error; case "sfmd": return Error; case "sfsb": return Error; case "sfsf": return Error; case "sfsm": return Error; case "sfss": return Error; case "sfsd": return Error; case "sfdb": return Error; case "sfdf": return Error; case "sfdm": return Error; case "sfds": return Error; case "sfdd": return Error; case "smbb": return Error; case "smbf": return Error; case "smbm": return Error; case "smbs": return Error; case "smbd": return Error; case "smfb": return Error; case "smff": return Error; case "smfm": return Error; case "smfs": return Error; case "smfd": return Error; case "smmb": return Error; case "smmf": return Error; case "smmm": return Error; case "smms": return Error; case "smmd": return Error; case "smsb": return Error; case "smsf": return Error; case "smsm": return Error; case "smss": return Error; case "smsd": return Error; case "smdb": return Error; case "smdf": return Error; case "smdm": return Error; case "smds": return Error; case "smdd": return Error; case "ssbb": return Error; case "ssbf": return Error; case "ssbm": return Error; case "ssbs": return Error; case "ssbd": return Error; case "ssfb": return Error; case "ssff": return Error; case "ssfm": return Error; case "ssfs": return Error; case "ssfd": return Error; case "ssmb": return Error; case "ssmf": return Error; case "ssmm": return Error; case "ssms": return Error; case "ssmd": return Error; case "sssb": return Error; case "sssf": return Error; case "sssm": return Error; case "ssss": return Error; case "sssd": return Error; case "ssdb": return Error; case "ssdf": return Error; case "ssdm": return Error; case "ssds": return Error; case "ssdd": return Error; case "sdbb": return Error; case "sdbf": return Error; case "sdbm": return Error; case "sdbs": return Error; case "sdbd": return Error; case "sdfb": return Error; case "sdff": return Error; case "sdfm": return Error; case "sdfs": return Error; case "sdfd": return Error; case "sdmb": return Error; case "sdmf": return Error; case "sdmm": return Error; case "sdms": return Error; case "sdmd": return Error; case "sdsb": return Error; case "sdsf": return Error; case "sdsm": return Error; case "sdss": return Error; case "sdsd": return Error; case "sddb": return Error; case "sddf": return Error; case "sddm": return Error; case "sdds": return Error; case "sddd": return Error; case "dbbb": return Error; case "dbbf": return Error; case "dbbm": return Error; case "dbbs": return Error; case "dbbd": return Error; case "dbfb": return Error; case "dbff": return Error; case "dbfm": return Error; case "dbfs": return Error; case "dbfd": return Error; case "dbmb": return Error; case "dbmf": return Error; case "dbmm": return Error; case "dbms": return Error; case "dbmd": return Error; case "dbsb": return Error; case "dbsf": return Error; case "dbsm": return Error; case "dbss": return Error; case "dbsd": return Error; case "dbdb": return Error; case "dbdf": return Error; case "dbdm": return Error; case "dbds": return Error; case "dbdd": return Error; case "dfbb": return Error; case "dfbf": return Error; case "dfbm": return Error; case "dfbs": return Error; case "dfbd": return Error; case "dffb": return Error; case "dfff": return Error; case "dffm": return Error; case "dffs": return Error; case "dffd": return Error; case "dfmb": return Error; case "dfmf": return Error; case "dfmm": return Error; case "dfms": return Error; case "dfmd": return Error; case "dfsb": return Error; case "dfsf": return Error; case "dfsm": return Error; case "dfss": return Error; case "dfsd": return Error; case "dfdb": return Error; case "dfdf": return Error; case "dfdm": return Error; case "dfds": return Error; case "dfdd": return Error; case "dmbb": return Error; case "dmbf": return Error; case "dmbm": return Error; case "dmbs": return Error; case "dmbd": return Error; case "dmfb": return Error; case "dmff": return Error; case "dmfm": return Error; case "dmfs": return Error; case "dmfd": return Error; case "dmmb": return Error; case "dmmf": return Error; case "dmmm": return Error; case "dmms": return Error; case "dmmd": return Error; case "dmsb": return Error; case "dmsf": return Error; case "dmsm": return Error; case "dmss": return Error; case "dmsd": return Error; case "dmdb": return Error; case "dmdf": return Error; case "dmdm": return Error; case "dmds": return Error; case "dmdd": return Error; case "dsbb": return Error; case "dsbf": return Error; case "dsbm": return Error; case "dsbs": return Error; case "dsbd": return Error; case "dsfb": return Error; case "dsff": return Error; case "dsfm": return Error; case "dsfs": return Error; case "dsfd": return Error; case "dsmb": return Error; case "dsmf": return Error; case "dsmm": return Error; case "dsms": return Error; case "dsmd": return Error; case "dssb": return Error; case "dssf": return Error; case "dssm": return Error; case "dsss": return Error; case "dssd": return Error; case "dsdb": return Error; case "dsdf": return Error; case "dsdm": return Error; case "dsds": return Error; case "dsdd": return Error; case "ddbb": return Error; case "ddbf": return Error; case "ddbm": return Error; case "ddbs": return Error; case "ddbd": return Error; case "ddfb": return Error; case "ddff": return Error; case "ddfm": return Error; case "ddfs": return Error; case "ddfd": return Error; case "ddmb": return Error; case "ddmf": return Error; case "ddmm": return Error; case "ddms": return Error; case "ddmd": return Error; case "ddsb": return Error; case "ddsf": return Error; case "ddsm": return Error; case "ddss": return Error; case "ddsd": return Error; case "dddb": return Error; case "dddf": return Error; case "dddm": return Error; case "ddds": return Error;
                        case "dddd": return Error;
                        default:
                            throw new NotImplementedException();
                    }
                default:
                    throw new NotImplementedException();
            }
        }
    }
}
