/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-12.3.2-MariaDB, for Linux (x86_64)
--
-- Host: localhost    Database: epartes_local
-- ------------------------------------------------------
-- Server version	12.3.2-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `areaspayroll`
--

DROP TABLE IF EXISTS `areaspayroll`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `areaspayroll` (
  `CODE` int(11) NOT NULL,
  `NAME` varchar(50) NOT NULL,
  `SYNCRONIZED_A3` bit(1) DEFAULT b'0',
  `SYNCRONIZED_A3_DATE` date DEFAULT NULL,
  PRIMARY KEY (`CODE`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `areaspayroll`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `areaspayroll` WRITE;
/*!40000 ALTER TABLE `areaspayroll` DISABLE KEYS */;
INSERT INTO `areaspayroll` VALUES
(100,'Desarrollo Software',0x00,NULL),
(200,'Mantenimiento y Planta',0x00,NULL);
/*!40000 ALTER TABLE `areaspayroll` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `departmentspayroll`
--

DROP TABLE IF EXISTS `departmentspayroll`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `departmentspayroll` (
  `CODE` int(11) NOT NULL,
  `NAME` varchar(100) DEFAULT NULL,
  `DESCRIPTION` varchar(100) DEFAULT NULL,
  `ACTIVE` bit(1) DEFAULT b'1',
  `SYNCRONIZED_A3` bit(1) DEFAULT b'0',
  `SYNCRONIZED_A3_DATE` date DEFAULT NULL,
  PRIMARY KEY (`CODE`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `departmentspayroll`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `departmentspayroll` WRITE;
/*!40000 ALTER TABLE `departmentspayroll` DISABLE KEYS */;
INSERT INTO `departmentspayroll` VALUES
(10,'Sistemas e IT','Departamento de Tecnología y Desarrollo',0x01,0x00,NULL),
(20,'Operaciones','Departamento de Operaciones de Planta',0x01,0x00,NULL);
/*!40000 ALTER TABLE `departmentspayroll` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `eppartstatus`
--

DROP TABLE IF EXISTS `eppartstatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `eppartstatus` (
  `STATUS` char(1) NOT NULL,
  `DESCRIPTION` varchar(100) NOT NULL,
  `COLOR` char(7) NOT NULL,
  PRIMARY KEY (`STATUS`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `eppartstatus`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `eppartstatus` WRITE;
/*!40000 ALTER TABLE `eppartstatus` DISABLE KEYS */;
INSERT INTO `eppartstatus` VALUES
('A','Creado por el encargado','#FF8040'),
('B','Creado por el empleado','#FF0000'),
('C','Visto bueno por el jefe de área','#00FF00'),
('D','Modificado y visto bueno por el jefe de área','#FF0080'),
('E','Firmado por el jefe de departamento','#299999'),
('F','Modificado y firmado por el jefe de departamento.','#800080'),
('G','Traspasado a nómina por RRHH','#00FFFF'),
('H','Modificado por RRHH','#666699'),
('I','Modificado por RRHH y traspasado a nómina por RRHH','#0000FF');
/*!40000 ALTER TABLE `eppartstatus` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `grupospayroll`
--

DROP TABLE IF EXISTS `grupospayroll`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `grupospayroll` (
  `CODE` int(11) NOT NULL,
  `EXTERNALCODE` int(11) NOT NULL,
  `NAME` varchar(100) DEFAULT NULL,
  `SYNCRONIZED_A3` bit(1) DEFAULT b'0',
  `SYNCRONIZED_A3_DATE` date DEFAULT NULL,
  PRIMARY KEY (`CODE`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grupospayroll`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `grupospayroll` WRITE;
/*!40000 ALTER TABLE `grupospayroll` DISABLE KEYS */;
INSERT INTO `grupospayroll` VALUES
(1,1001,'Grupo Técnico A',0x00,NULL),
(2,1002,'Grupo Operativo B',0x00,NULL);
/*!40000 ALTER TABLE `grupospayroll` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `tep_classificationpayroll`
--

DROP TABLE IF EXISTS `tep_classificationpayroll`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tep_classificationpayroll` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `CLASSIFICATION_SUMMARY` varchar(20) NOT NULL,
  `CLASSIFICATION_DESCRIPTION` varchar(250) NOT NULL,
  `IS_SYNCHRONIZED` bit(1) DEFAULT b'0',
  `SYNCHRONIZED_DATE` date DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tep_classificationpayroll`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `tep_classificationpayroll` WRITE;
/*!40000 ALTER TABLE `tep_classificationpayroll` DISABLE KEYS */;
/*!40000 ALTER TABLE `tep_classificationpayroll` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `userpayroll`
--

DROP TABLE IF EXISTS `userpayroll`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `userpayroll` (
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,
  `NUMPER` varchar(8) NOT NULL,
  `NAME` varchar(50) NOT NULL,
  `SURNAME` varchar(50) DEFAULT NULL,
  `PASSWORD` varchar(60) DEFAULT NULL,
  `PASSWORD1` varchar(60) DEFAULT NULL,
  `PASSWORD2` varchar(60) DEFAULT NULL,
  `EMAIL` varchar(100) DEFAULT NULL,
  `NUMHUELLA` varchar(8) DEFAULT NULL,
  `UUID` binary(16) DEFAULT NULL,
  `PW_REFRESH_TOKEN` varchar(255) DEFAULT NULL,
  `TOKEN_EXPIRATION` varchar(255) DEFAULT NULL,
  `ACTIVE` bit(1) DEFAULT NULL,
  `DEPARTMENT` int(11) DEFAULT NULL,
  `IDENTIFIER_NUMBER` varchar(9) DEFAULT NULL,
  `AREA` int(11) DEFAULT NULL,
  `CLASSIFICATION_ID` bigint(20) DEFAULT NULL,
  `ASSIGNED_TURN` varchar(250) DEFAULT NULL,
  `IS_SYNCHRONIZED` bit(1) DEFAULT b'0',
  `SYNCHRONIZED_DATE` date DEFAULT NULL,
  `GRUPO` int(11) DEFAULT 0,
  PRIMARY KEY (`ID`),
  KEY `user_AREA_IDX` (`AREA`),
  KEY `user_CLASSIFICATION_ID_IDX` (`CLASSIFICATION_ID`),
  KEY `user_DEPARTMENT_IDX` (`DEPARTMENT`),
  KEY `user_GRUPO_IDX` (`GRUPO`),
  KEY `userpayroll_NUMPER_IDX` (`NUMPER`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `userpayroll`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `userpayroll` WRITE;
/*!40000 ALTER TABLE `userpayroll` DISABLE KEYS */;
INSERT INTO `userpayroll` VALUES
(1,'00000001','Juan','Pérez Gómez','123456',NULL,NULL,'jperez@empresa.local',NULL,NULL,NULL,NULL,0x01,10,NULL,100,NULL,NULL,0x00,NULL,1),
(2,'00000002','María','García López','123456',NULL,NULL,'mgarcia@empresa.local',NULL,NULL,NULL,NULL,0x01,10,NULL,100,NULL,NULL,0x00,NULL,1),
(3,'00000003','Carlos','Rodríguez Silva','123456',NULL,NULL,'crodriguez@empresa.local',NULL,NULL,NULL,NULL,0x01,20,NULL,200,NULL,NULL,0x00,NULL,2);
/*!40000 ALTER TABLE `userpayroll` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `zgrroles`
--

DROP TABLE IF EXISTS `zgrroles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `zgrroles` (
  `CODGR` int(11) NOT NULL,
  `PERNR` varchar(8) NOT NULL,
  `ROLNAME` varchar(2) NOT NULL,
  PRIMARY KEY (`CODGR`,`PERNR`,`ROLNAME`),
  UNIQUE KEY `zgrroles_unique` (`CODGR`,`PERNR`,`ROLNAME`),
  KEY `ZGRROLES_GROUP_IDX` (`CODGR`),
  KEY `idx_Zgrroles_pernr` (`PERNR`),
  KEY `idx_Zgrroles_pernr_rol` (`PERNR`,`ROLNAME`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `zgrroles`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `zgrroles` WRITE;
/*!40000 ALTER TABLE `zgrroles` DISABLE KEYS */;
INSERT INTO `zgrroles` VALUES
(1,'00000001','EM'),
(1,'00000002','JA'),
(2,'00000003','EM');
/*!40000 ALTER TABLE `zgrroles` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `zparte`
--

DROP TABLE IF EXISTS `zparte`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `zparte` (
  `MANDT` bigint(20) NOT NULL,
  `PERNR` varchar(8) NOT NULL,
  `PADAT` date NOT NULL,
  `TIPO` varchar(1) NOT NULL,
  `TURNO` varchar(1) NOT NULL,
  `REDAT` date DEFAULT NULL,
  `UPDAT` date DEFAULT NULL,
  `MODIF` varchar(1) DEFAULT NULL,
  `MES` varchar(2) DEFAULT NULL,
  `EJERC` varchar(4) DEFAULT NULL,
  `STAT` varchar(1) DEFAULT NULL,
  `TPRE1` varchar(4) DEFAULT NULL,
  `TPRE2` varchar(4) DEFAULT NULL,
  `PAJOB` varchar(1) DEFAULT NULL,
  `CODGR` int(11) DEFAULT 0,
  `DPTO` varchar(150) DEFAULT NULL,
  `CATEG` varchar(20) DEFAULT NULL,
  `TREALIZ` varchar(35) DEFAULT NULL,
  `TIPODIA` varchar(1) DEFAULT NULL,
  `PERNRCR` varchar(8) DEFAULT NULL,
  `CRDAT` date DEFAULT NULL,
  `PERNRVB` varchar(8) DEFAULT NULL,
  `VBDAT` date DEFAULT NULL,
  `PERNRFI` varchar(8) DEFAULT NULL,
  `FIDAT` date DEFAULT NULL,
  `PERNRHR` varchar(8) DEFAULT NULL,
  `HRDAT` date DEFAULT NULL,
  `HN` int(11) DEFAULT 0,
  `HP` int(11) DEFAULT 0,
  `DL` int(11) DEFAULT 0,
  `DF` int(11) DEFAULT 0,
  `NL` int(11) DEFAULT 0,
  `NF` int(11) DEFAULT 0,
  `DLB` int(11) DEFAULT 0,
  `DFB` int(11) DEFAULT 0,
  `NLB` int(11) DEFAULT 0,
  `NFB` int(11) DEFAULT 0,
  `DLF` int(11) DEFAULT 0,
  `DFF` int(11) DEFAULT 0,
  `NLF` int(11) DEFAULT 0,
  `NFF` int(11) DEFAULT 0,
  `DLC` int(11) DEFAULT 0,
  `DFC` int(11) DEFAULT 0,
  `NLC` int(11) DEFAULT 0,
  `NFC` int(11) DEFAULT 0,
  `LLDL` int(11) DEFAULT 0,
  `LLDF` int(11) DEFAULT 0,
  `LLNL` int(11) DEFAULT 0,
  `LLNF` int(11) DEFAULT 0,
  `DLCO` int(11) DEFAULT 0,
  `DFCO` int(11) DEFAULT 0,
  `NLCO` int(11) DEFAULT 0,
  `NFCO` int(11) DEFAULT 0,
  `DLBN` int(11) DEFAULT 0,
  `DFBN` int(11) DEFAULT 0,
  `NLBN` int(11) DEFAULT 0,
  `NFBN` int(11) DEFAULT 0,
  `DLCOP` int(11) DEFAULT 0,
  `DFCOP` int(11) DEFAULT 0,
  `NLCOP` int(11) DEFAULT 0,
  `NFCOP` int(11) DEFAULT 0,
  `MOTIVOHE` varchar(150) DEFAULT NULL,
  `MOTIVOHEB` varchar(150) DEFAULT NULL,
  `MOTIVOHP` varchar(150) DEFAULT NULL,
  `MOTIVOHEC` varchar(150) DEFAULT NULL,
  `MOTIVOLLA` varchar(150) DEFAULT NULL,
  `MOTIVOHFM` varchar(150) DEFAULT NULL,
  `MOTHECO` varchar(150) DEFAULT NULL,
  `MOTHEBNP` varchar(150) DEFAULT NULL,
  `MOTHECOP` varchar(150) DEFAULT NULL,
  `SP` char(1) DEFAULT NULL,
  `CP` char(1) DEFAULT NULL,
  `PP` char(1) DEFAULT NULL,
  `B` char(1) DEFAULT NULL,
  `D` char(1) DEFAULT NULL,
  `DD` char(1) DEFAULT NULL,
  `KM` int(11) DEFAULT NULL,
  `P52` char(1) DEFAULT NULL,
  `P60` char(1) DEFAULT NULL,
  `BLV` char(1) DEFAULT NULL,
  `BSDF` char(1) DEFAULT NULL,
  `CPT` char(1) DEFAULT NULL,
  `PN` char(1) DEFAULT NULL,
  `PA` char(1) DEFAULT NULL,
  `NI020` char(1) DEFAULT NULL,
  `OBSERV` varchar(150) DEFAULT NULL,
  `SUST` char(1) DEFAULT NULL,
  `SUPERN` varchar(8) DEFAULT NULL,
  `SUPERN1` varchar(8) DEFAULT NULL,
  `MOTIVOSUST` varchar(150) DEFAULT NULL,
  `NH` int(11) DEFAULT 0,
  `OBSERV1` varchar(150) DEFAULT NULL,
  `HNDEC` varchar(6) DEFAULT '000000',
  `TIPOTURNO` int(11) DEFAULT 0,
  `TELETRABAJO` char(1) DEFAULT 'f',
  `DESCANSO` char(1) DEFAULT 'f',
  `ART21DESC` char(1) DEFAULT 'f',
  `TURNOSUSTIT` varchar(80) DEFAULT NULL,
  `USER_ID` varchar(8) NOT NULL DEFAULT '00000000',
  `PERVBDE` varchar(8) DEFAULT NULL,
  `PERFIDE` varchar(8) DEFAULT NULL,
  `STATPREV` varchar(1) DEFAULT '',
  PRIMARY KEY (`MANDT`,`PERNR`,`PADAT`,`TIPO`,`TURNO`),
  UNIQUE KEY `zparte_MANDT_IDX` (`MANDT`),
  UNIQUE KEY `idx_unico_persona_dia` (`PERNR`,`PADAT`,`TIPO`,`TURNO`),
  KEY `ZPARTE_GROUP_IDX` (`CODGR`),
  KEY `ZPARTE_dpto_IDX` (`DPTO`),
  KEY `ZPARTE_CATEG_IDX` (`CATEG`),
  KEY `ZPARTE_USER_IDX` (`USER_ID`),
  KEY `idx_ejer_month` (`EJERC`,`MES`),
  KEY `idx_mes_ejer` (`MES`,`EJERC`),
  KEY `idx_mes_padat` (`PADAT`),
  KEY `idx_mes_mes_ejerc_padat` (`MES`,`EJERC`,`PADAT`),
  KEY `idx_Zparte_pernr_group` (`PERNR`,`CODGR`),
  KEY `idx_zparte_ejerc` (`EJERC`),
  KEY `idx_zparte_ejerc_codgr` (`EJERC`,`CODGR`),
  KEY `idx_zparte_codgr` (`CODGR`),
  KEY `zparte_PERNR_IDX` (`PERNR`,`PADAT`),
  KEY `idx_updat` (`UPDAT`),
  KEY `idx_zparte_pervbde` (`PERVBDE`),
  KEY `idx_zparte_perfide` (`PERFIDE`),
  KEY `idx_zparte_ejerc_mes_codgr` (`EJERC`,`MES`,`CODGR`),
  KEY `zparte_PERNR_MES_EJERC_IDX` (`PERNR`,`MES`,`EJERC`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `zparte`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `zparte` WRITE;
/*!40000 ALTER TABLE `zparte` DISABLE KEYS */;
INSERT INTO `zparte` VALUES
(1786358400000,'00000001','2026-08-10','N','M',NULL,NULL,NULL,'08','2026','A',NULL,NULL,NULL,1,'Sistemas e IT','Analista Programador',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,8,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'Soporte despliegue fuera de horario',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'000000',0,'f','f','f',NULL,'00000001',NULL,NULL,''),
(1786358400001,'00000003','2026-08-10','N','T',NULL,NULL,NULL,'08','2026','B',NULL,NULL,NULL,2,'Operaciones','Técnico de Planta',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,8,4,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'Mantenimiento correctivo urgente',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'000000',0,'f','f','f',NULL,'00000003',NULL,NULL,''),
(1786444800000,'00000001','2026-08-11','N','M',NULL,NULL,NULL,'08','2026','C',NULL,NULL,NULL,1,'Sistemas e IT','Analista Programador',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'000000',0,'f','f','f',NULL,'00000001',NULL,NULL,'A');
/*!40000 ALTER TABLE `zparte` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;

--
-- Table structure for table `zperiodos`
--

DROP TABLE IF EXISTS `zperiodos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `zperiodos` (
  `ID` varchar(2) NOT NULL,
  `EJERCICIO` varchar(4) NOT NULL,
  `DESCRIPTION` varchar(255) DEFAULT NULL,
  `FECHAINI` date DEFAULT NULL,
  `FECHAFIN` date DEFAULT NULL,
  `FEVBUFIN` date DEFAULT NULL,
  `FEFIRFIN` date DEFAULT NULL,
  `TRASPASO` varchar(1) DEFAULT NULL,
  PRIMARY KEY (`ID`,`EJERCICIO`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `zperiodos`
--

SET @OLD_AUTOCOMMIT=@@AUTOCOMMIT, @@AUTOCOMMIT=0;
LOCK TABLES `zperiodos` WRITE;
/*!40000 ALTER TABLE `zperiodos` DISABLE KEYS */;
INSERT INTO `zperiodos` VALUES
('08','2026','Agosto 2026','2026-08-01','2026-08-31','2026-09-05','2026-09-10','0');
/*!40000 ALTER TABLE `zperiodos` ENABLE KEYS */;
UNLOCK TABLES;
COMMIT;
SET AUTOCOMMIT=@OLD_AUTOCOMMIT;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2026-09-07 19:36:39
