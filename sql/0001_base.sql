-- Hold top level zone file
RECREATE TABLE zone_files
(
    id int NOT NULL PRIMARY KEY,
    origin varchar(255) NOT NULL,
    soa int NOT NULL
);

-- Hold domains
RECREATE TABLE domains
(
    id int NOT NULL PRIMARY KEY,
    zone_file int NOT NULL,
    domain_name varchar(255) NOT NULL UNIQUE,
    FOREIGN KEY (zone_file) REFERENCES zone_files(id) ON DELETE CASCADE
);

-- Holds nameservers seen, references to domain (special handling for NS records)
RECREATE TABLE nameservers
(
    id int NOT NULL PRIMARY KEY,
    zone_file int NOT NULL,
    domain_name varchar(255) NOT NULL UNIQUE,
    FOREIGN KEY (zone_file) REFERENCES zone_files(id) ON DELETE CASCADE
);

-- Link table between domains and nameservers
RECREATE TABLE domain_nameservers
(
    id int NOT NULL PRIMARY KEY,
    domain_id int NOT NULL,
    nameserver_id int NOT NULL REFERENCES nameservers(id),
    FOREIGN KEY (domain_id) REFERENCES domains(id) ON DELETE CASCADE,
    FOREIGN KEY (nameserver_id) REFERENCES nameservers(id) ON DELETE CASCADE
);

-- Holds domain rrdata
RECREATE TABLE domain_rdata
(
    id int NOT NULL PRIMARY KEY,
    domain_id int NOT NULL,
    rrtype varchar(10) NOT NULL, -- 10 might be too long here but whatever
    rdata blob NOT NULL,
    FOREIGN KEY (domain_id) REFERENCES domains(id) ON DELETE CASCADE
);

-- Hold reverse zone information
RECREATE TABLE ptr_records
(
    id int NOT NULL PRIMARY KEY,
    domain_id int NOT NULL,
    ptr varchar(255) NOT NULL UNIQUE,
    FOREIGN KEY (domain_id) REFERENCES domains(id) ON DELETE CASCADE
);