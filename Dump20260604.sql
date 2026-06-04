-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: localhost    Database: crm_db
-- ------------------------------------------------------
-- Server version	8.0.45

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `client`
--

DROP TABLE IF EXISTS `client`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `client` (
  `client_id` int NOT NULL AUTO_INCREMENT,
  `client_name` varchar(100) DEFAULT NULL,
  `monitor_present` enum('YES','NO') DEFAULT NULL,
  `property_type` varchar(200) DEFAULT NULL,
  `address` text,
  `location_link` text,
  `nearest_metrostation` varchar(100) DEFAULT NULL,
  `mail_id` varchar(100) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `mobile_no` varchar(20) DEFAULT NULL,
  `product` varchar(200) DEFAULT NULL,
  `installation_date` date DEFAULT NULL,
  `activation_date` date DEFAULT NULL,
  `filter_colour` varchar(50) DEFAULT NULL,
  `no_of_units_installed` int DEFAULT NULL,
  `solution_working` enum('YES','NO') DEFAULT NULL,
  `cmc_applicable` enum('YES','NO') DEFAULT NULL,
  `cmc_due_days` int DEFAULT NULL,
  `cmc_due` enum('YES','NO') DEFAULT NULL,
  `next_cmc_renewal_date` date DEFAULT NULL,
  `cmc_amount` decimal(10,2) DEFAULT NULL,
  `last_service_days` int DEFAULT NULL,
  `last_service_date` date DEFAULT NULL,
  `service_interval_days` int DEFAULT '30',
  `service_due` enum('YES','NO') DEFAULT NULL,
  `filter_clean` enum('YES','NO') DEFAULT NULL,
  `service_for` varchar(200) DEFAULT NULL,
  `no_of_filters_replaced` int DEFAULT NULL,
  `pre_service_msg` enum('YES','NO') DEFAULT NULL,
  `post_service_msg` enum('YES','NO') DEFAULT NULL,
  `remark` text,
  `proposal_id` int DEFAULT NULL,
  `invoice_id` int DEFAULT NULL,
  PRIMARY KEY (`client_id`),
  KEY `fk_client_proposal` (`proposal_id`),
  KEY `fk_client_invoice` (`invoice_id`),
  CONSTRAINT `fk_client_invoice` FOREIGN KEY (`invoice_id`) REFERENCES `invoices` (`invoice_id`),
  CONSTRAINT `fk_client_proposal` FOREIGN KEY (`proposal_id`) REFERENCES `proposals` (`proposal_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client`
--

LOCK TABLES `client` WRITE;
/*!40000 ALTER TABLE `client` DISABLE KEYS */;
/*!40000 ALTER TABLE `client` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `customer_care_card`
--

DROP TABLE IF EXISTS `customer_care_card`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer_care_card` (
  `card_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int DEFAULT NULL,
  `service_date` date DEFAULT NULL,
  `service_of` varchar(100) DEFAULT NULL,
  `no_of_filters` int DEFAULT NULL,
  `controller_changed` enum('YES','NO') DEFAULT NULL,
  `fan_changed` enum('YES','NO') DEFAULT NULL,
  `serviced_by` varchar(100) DEFAULT NULL,
  `pre_service_msgd` enum('YES','NO') DEFAULT NULL,
  `post_service_report_sent` enum('YES','NO') DEFAULT NULL,
  `miscellaneous_messages` text,
  `tips_and_tricks` text,
  `referrals_program` varchar(100) DEFAULT NULL,
  `news_sent` enum('YES','NO') DEFAULT NULL,
  `communication_date` date DEFAULT NULL,
  `remark` text,
  PRIMARY KEY (`card_id`),
  KEY `client_id` (`client_id`),
  CONSTRAINT `customer_care_card_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `client` (`client_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customer_care_card`
--

LOCK TABLES `customer_care_card` WRITE;
/*!40000 ALTER TABLE `customer_care_card` DISABLE KEYS */;
/*!40000 ALTER TABLE `customer_care_card` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `drawings`
--

DROP TABLE IF EXISTS `drawings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `drawings` (
  `drawing_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `address` text,
  `iterations` int DEFAULT NULL,
  `moca` varchar(100) DEFAULT NULL,
  `drawing_pdf` varchar(255) DEFAULT NULL,
  `visit_id` int DEFAULT NULL,
  PRIMARY KEY (`drawing_id`),
  KEY `fk_drawing_visit` (`visit_id`),
  CONSTRAINT `fk_drawing_visit` FOREIGN KEY (`visit_id`) REFERENCES `visits` (`visit_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `drawings`
--

LOCK TABLES `drawings` WRITE;
/*!40000 ALTER TABLE `drawings` DISABLE KEYS */;
/*!40000 ALTER TABLE `drawings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `invoices`
--

DROP TABLE IF EXISTS `invoices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `invoices` (
  `invoice_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `doi` date DEFAULT NULL,
  `invoice_no` varchar(100) DEFAULT NULL,
  `gst_no` varchar(50) DEFAULT NULL,
  `product_sold` varchar(200) DEFAULT NULL,
  `total_units` int DEFAULT NULL,
  `price_of_units` decimal(12,2) DEFAULT NULL,
  `first_year_cmc` decimal(12,2) DEFAULT NULL,
  `installation` decimal(12,2) DEFAULT NULL,
  `total_sensor` int DEFAULT NULL,
  `sensor_cost` decimal(12,2) DEFAULT NULL,
  `revenue` decimal(12,2) DEFAULT NULL,
  `total_revenue` decimal(12,2) DEFAULT NULL,
  `sales_id` int DEFAULT NULL,
  `invoice_pdf` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`invoice_id`),
  KEY `fk_invoice_sales` (`sales_id`),
  CONSTRAINT `fk_invoice_sales` FOREIGN KEY (`sales_id`) REFERENCES `sales_pipeline` (`sales_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `invoices`
--

LOCK TABLES `invoices` WRITE;
/*!40000 ALTER TABLE `invoices` DISABLE KEYS */;
/*!40000 ALTER TABLE `invoices` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leads`
--

DROP TABLE IF EXISTS `leads`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leads` (
  `lead_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `reference` varchar(200) DEFAULT NULL,
  `location` varchar(200) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `responses` text,
  `date_of_1st_followup` date DEFAULT NULL,
  `next_to_call` date DEFAULT NULL,
  `recent` text,
  PRIMARY KEY (`lead_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `leads`
--

LOCK TABLES `leads` WRITE;
/*!40000 ALTER TABLE `leads` DISABLE KEYS */;
/*!40000 ALTER TABLE `leads` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `meetings`
--

DROP TABLE IF EXISTS `meetings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `meetings` (
  `meeting_id` int NOT NULL AUTO_INCREMENT,
  `meeting_fixed_by` varchar(100) DEFAULT NULL,
  `source` varchar(100) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `reference` varchar(200) DEFAULT NULL,
  `firm_name` varchar(200) DEFAULT NULL,
  `designation` varchar(100) DEFAULT NULL,
  `address` text,
  `state` varchar(100) DEFAULT NULL,
  `contact_no` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `company_info_shared` enum('YES','NO') DEFAULT NULL,
  `meeting_fixed` enum('YES','NO') DEFAULT NULL,
  `date_of_meeting` date DEFAULT NULL,
  `mode_of_meeting` varchar(50) DEFAULT NULL,
  `meeting_status` varchar(50) DEFAULT NULL,
  `meeting_conducted_by` varchar(100) DEFAULT NULL,
  `floor_plan_shared` enum('YES','NO') DEFAULT NULL,
  `site_visit` enum('YES','NO') DEFAULT NULL,
  `post_meeting_mail` enum('YES','NO') DEFAULT NULL,
  `date_of_last_followup` date DEFAULT NULL,
  `date_to_call_next` date DEFAULT NULL,
  `final_remarks` text,
  `reschedule_date` date DEFAULT NULL,
  `reason_for_reschedule` text,
  `remarks` text,
  `lead_id` int DEFAULT NULL,
  PRIMARY KEY (`meeting_id`),
  KEY `fk_meeting_lead` (`lead_id`),
  CONSTRAINT `fk_meeting_lead` FOREIGN KEY (`lead_id`) REFERENCES `leads` (`lead_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `meetings`
--

LOCK TABLES `meetings` WRITE;
/*!40000 ALTER TABLE `meetings` DISABLE KEYS */;
/*!40000 ALTER TABLE `meetings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `proposals`
--

DROP TABLE IF EXISTS `proposals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `proposals` (
  `proposal_id` int NOT NULL AUTO_INCREMENT,
  `reference_no` varchar(50) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `phone_no_client` varchar(20) DEFAULT NULL,
  `source` varchar(100) DEFAULT NULL,
  `type` varchar(100) DEFAULT NULL,
  `reference_source_details` text,
  `phone_no_source` varchar(20) DEFAULT NULL,
  `contact_person` varchar(100) DEFAULT NULL,
  `phone_no_contact_person` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `site_address` text,
  `state` varchar(100) DEFAULT NULL,
  `total_area_sqft` decimal(10,2) DEFAULT NULL,
  `type_of_units` varchar(100) DEFAULT NULL,
  `no_of_mvd_units` int DEFAULT NULL,
  `no_of_mvd_max_units` int DEFAULT NULL,
  `total_no_of_units` int DEFAULT NULL,
  `product` varchar(200) DEFAULT NULL,
  `cost_total_per_unit` decimal(10,2) DEFAULT NULL,
  `no_of_monitors` int DEFAULT NULL,
  `cmc` enum('YES','NO') DEFAULT NULL,
  `per_unit_cost` decimal(10,2) DEFAULT NULL,
  `per_unit_cost_max_unit` decimal(10,2) DEFAULT NULL,
  `cmc_cost` decimal(10,2) DEFAULT NULL,
  `monitor_cost` decimal(10,2) DEFAULT NULL,
  `installation_cost` decimal(10,2) DEFAULT NULL,
  `total_amount` decimal(12,2) DEFAULT NULL,
  `cmc_starting_period` varchar(100) DEFAULT NULL,
  `discount` decimal(10,2) DEFAULT NULL,
  `final_amount` decimal(12,2) DEFAULT NULL,
  `date_of_proposal_sent` date DEFAULT NULL,
  `proposal_prepared_by` varchar(100) DEFAULT NULL,
  `proposal_shared_by` varchar(100) DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `date_of_last_followup` date DEFAULT NULL,
  `next_to_call` date DEFAULT NULL,
  `remarks` text,
  `proposal_pdf` varchar(255) DEFAULT NULL,
  `meeting_id` int DEFAULT NULL,
  `drawing_id` int DEFAULT NULL,
  PRIMARY KEY (`proposal_id`),
  KEY `fk_proposal_meeting` (`meeting_id`),
  KEY `fk_proposal_drawing` (`drawing_id`),
  CONSTRAINT `fk_proposal_drawing` FOREIGN KEY (`drawing_id`) REFERENCES `drawings` (`drawing_id`),
  CONSTRAINT `fk_proposal_meeting` FOREIGN KEY (`meeting_id`) REFERENCES `meetings` (`meeting_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `proposals`
--

LOCK TABLES `proposals` WRITE;
/*!40000 ALTER TABLE `proposals` DISABLE KEYS */;
/*!40000 ALTER TABLE `proposals` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sales_pipeline`
--

DROP TABLE IF EXISTS `sales_pipeline`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sales_pipeline` (
  `sales_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `reference_no` varchar(50) DEFAULT NULL,
  `project_stage` varchar(100) DEFAULT NULL,
  `moc` varchar(100) DEFAULT NULL,
  `source` varchar(100) DEFAULT NULL,
  `next_action` text,
  `address` text,
  `contact_no` varchar(20) DEFAULT NULL,
  `project_type` varchar(100) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `email_id` varchar(100) DEFAULT NULL,
  `site_incharge` varchar(100) DEFAULT NULL,
  `site_incharge_contact` varchar(20) DEFAULT NULL,
  `first_contact` date DEFAULT NULL,
  `last_contact` date DEFAULT NULL,
  `followup_date` date DEFAULT NULL,
  `no_of_site_visits` int DEFAULT NULL,
  `area_covered` decimal(12,2) DEFAULT NULL,
  `total_units` int DEFAULT NULL,
  `price_of_units` decimal(12,2) DEFAULT NULL,
  `first_year_cmc` decimal(12,2) DEFAULT NULL,
  `installation` decimal(12,2) DEFAULT NULL,
  `total_sensor` int DEFAULT NULL,
  `sensor_cost` decimal(12,2) DEFAULT NULL,
  `discount` decimal(12,2) DEFAULT NULL,
  `revenue` decimal(12,2) DEFAULT NULL,
  `amount_received` decimal(12,2) DEFAULT NULL,
  `amount_due` decimal(12,2) DEFAULT NULL,
  `total_revenue` decimal(12,2) DEFAULT NULL,
  `gst_no` varchar(50) DEFAULT NULL,
  `cmc_onwards` decimal(12,2) DEFAULT NULL,
  `total_cmc` decimal(12,2) DEFAULT NULL,
  `sales_person` varchar(100) DEFAULT NULL,
  `proposal_id` int DEFAULT NULL,
  PRIMARY KEY (`sales_id`),
  KEY `fk_sales_proposal` (`proposal_id`),
  CONSTRAINT `fk_sales_proposal` FOREIGN KEY (`proposal_id`) REFERENCES `proposals` (`proposal_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sales_pipeline`
--

LOCK TABLES `sales_pipeline` WRITE;
/*!40000 ALTER TABLE `sales_pipeline` DISABLE KEYS */;
/*!40000 ALTER TABLE `sales_pipeline` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(100) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `role` varchar(50) DEFAULT NULL,
  `full_name` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `is_active` enum('YES','NO') DEFAULT 'YES',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'admin','admin123','ADMIN',NULL,NULL,'YES');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `visits`
--

DROP TABLE IF EXISTS `visits`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `visits` (
  `visit_id` int NOT NULL AUTO_INCREMENT,
  `state` varchar(100) DEFAULT NULL,
  `region` varchar(100) DEFAULT NULL,
  `abc` varchar(100) DEFAULT NULL,
  `company_name` varchar(200) DEFAULT NULL,
  `person_name` varchar(100) DEFAULT NULL,
  `designation` varchar(100) DEFAULT NULL,
  `contact_no` varchar(20) DEFAULT NULL,
  `address` text,
  `brief` text,
  `visit_date` date DEFAULT NULL,
  `leads_generated` int DEFAULT NULL,
  `m2` text,
  `m3` text,
  `meeting_id` int DEFAULT NULL,
  PRIMARY KEY (`visit_id`),
  KEY `fk_visit_meeting` (`meeting_id`),
  CONSTRAINT `fk_visit_meeting` FOREIGN KEY (`meeting_id`) REFERENCES `meetings` (`meeting_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `visits`
--

LOCK TABLES `visits` WRITE;
/*!40000 ALTER TABLE `visits` DISABLE KEYS */;
/*!40000 ALTER TABLE `visits` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-04 16:39:15
