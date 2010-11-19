/* Drop table if exists */
DROP TABLE IF EXISTS `NOMACTX`;

/* Create the NOMACTX table */
CREATE TABLE `NOMACTX` (
  `account_code` int(20) DEFAULT NULL,
  `account_name` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `transaction_reference` int(20) DEFAULT NULL,
  `journal_code` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `date` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `third_party` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `comment1` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `comment2` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `tax_code` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `debit` float DEFAULT NULL,
  `credit` float DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

INSERT INTO `NOMACTX` VALUES (1100, 'Debtors Control Account', 1812, 'SR', '2009-01-06', 'OrgaNisma', '', 'Sales Receipt', 'Tax9', 0.0, 16892.2),(1100, 'Debtors Control Account', 2298, 'SI', '2009-01-05', 'NorgA', '25', 'Nov Outlay', 'Tax6', 741213.0, 0.0),(1100, 'Debtors Control Account', 2778, 'SA', '2009-03-11', 'NorgA', '', 'Payment on Account', 'Tax9', 0.0, 610204.0),(1100, 'Debtors Control Account', 4397, 'SC', '2009-06-17', 'NorgA', '47-1', 'Reverse Invoice 43', 'Tax6', 0.0, 477746.0),(1200, 'Bank Current Account', 1717, 'PP', '2009-01-02', 'MobileOrg', 'DD', 'Purchase Payment', 'Tax9', 0.0, 471.37),(1200, 'Bank Current Account', 1780, 'BP', '2009-01-05', 1200, 'DD', 'Lease # 01234', 'Tax6', 0.0,618.65),(1200, 'Bank Current Account', 1781, 'PA', '2009-01-06', 'Comporg', 'iBB', 'Payment on Account', 'Tax9', 0.0, 4070.25),(1200, 'Bank Current Account', 1812, 'SR', '2009-01-06', 'OrgaNisma', '', 'Sales Receipt', 'Tax9', 16892.2, 0.0),(1200, 'Bank Current Account', 2778, 'SA', '2009-03-11', 'NorgA', '', 'Payment on Account', 'Tax9', 610204.0, 0.0),(1200, 'Bank Current Account', 3049, 'BR', '2009-03-31', 1200, '518785', 'Return of goods to Elara', 'Tax6', 29.16, 0.0),(1230, 'Petty Cash', '2041', 'JC', '2009-01-02', 1230, 'Transporters', 'Error in posting payments', 'Tax9', 0.0, 58.38),(1231, 'Cash Advance - Quatre four', 2352, 'CP', '2009-02-16', 1231, 'Cash', 'Quatre four - Weekcomm 16/02/09', 'Tax0', 0.0, 896.0),(1240, 'Company Credit Card', 2036, 'JD', '2009-01-09', 1240, 'Transporters', 'Bank Transfer', 'Tax9', 463.87, 0.0),(1240, 'Company Credit Card', 2454, 'VP', '2009-01-19', 1240, 'COrg', 'Sat Nav and Motor Oil etc for Corg', 'Tax0', 0.0, 220.18),(2100, 'Creditors Control Account', 1690, 'PI', '2009-01-02', 'Telecom Supplier', '6', 'Calls to 31/12/08', 'Tax6', 0.0, 20.64),(2100, 'Creditors Control Account', 1717, 'PP', '2009-01-02', 'MobileOrg', 'DD', 'Purchase Payment', 'Tax9', 471.37, 0.0),(2100, 'Creditors Control Account', 1781, 'PA', '2009-01-06', 'Comporg', 'iBB', 'Payment on Account', 'Tax9', 4070.25, 0.0),(2100, 'Creditors Control Account', 2403, 'PC', '2009-02-27', 'MyCompTELEPE', '697', 'Against Oct Invoice 521069', 'Tax5', 20000.0, 0.0),(2200, 'Sales Tax Control Account', 2298, 'SI', '2009-01-05', 'NorgA', '25', 'Nov Outlay', 'Tax6', 0.0, 131161.0),(2200, 'Sales Tax Control Account', 3049, 'BR', '2009-03-31', 1200, '518785', 'Return of goods to Elara', 'Tax6', 0.0, 5.16),(2200, 'Sales Tax Control Account', 4397, 'SC', '2009-06-17', 'NorgA', '47-1', 'Reverse Invoice 43', 'Tax6', 84539.5, 0.0),(2201, 'Purchase Tax Control Account', 1690, 'PI', '2009-01-02', 'Telecom Supplier', '6', 'Calls to 31/12/08', 'Tax6', 3.65, 0.0),(2201, 'Purchase Tax Control Account', 1780, 'BP', '2009-01-05', 1200, 'DD', 'Lease # 01234', 'Tax6', 109.47, 0.0),(4004, 'Change request construction services', 4397, 'SC', '2009-06-17', 'NorgA', '47-1', 'Reverse Invoice 43', 'Tax6', 393207.0, 0.0),(5000, 'Purchases', 2298, 'SI', '2009-01-05', 'NorgA', '25', 'Nov Outlay', 'Tax6', 0.0, 610052.0),(5006, 'Contact Centre Services - MM Teleperformance', 2403, 'PC', '2009-02-27', 'MyCompTELEPE', '697', 'Against Oct Invoice 521069', 'Tax5', 0.0, 20000.0),(7301, 'Repairs and Servicing', 3049, 'BR', '2009-03-31', 1200, '518785', 'Return of goods to Elara', 'Tax6', 0.0, 24.0),(7304, 'Miscellaneous Motor Expenses', 1780, 'BP', '2009-01-05', 1200, 'DD', 'Lease # 01234', 'Tax6', 509.18, 0.0),(7304, 'Miscellaneous Motor Expenses', 2454, 'VP', '2009-01-19', 1240, 'Corg', 'Sat Nav and Motor Oil etc for Corg', 'Tax0', 220.18, 0.0),(7400, 'Travelling', 2352, 'CP', '2009-02-16', 1231, 'Cash', 'Quatre four - Weekcomm 16/02/09', 'Tax0', 896.0, 0.0),(7502, 'Telephone', 1690, 'PI', '2009-01-02', 'Telecom Supplier', '6', 'Calls to 31/12/08', 'Tax6', 16.99, 0.0);

