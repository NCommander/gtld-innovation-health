SELECT d.domain_name, d.status, rd.rrtype, rd.rdata
FROM DOMAINS AS d LEFT JOIN DOMAIN_RDATA AS rd ON (d.id=rd.domain_id)
WHERE RRTYPE IS NOT NULL;

SELECT (count(DPR.ptr_record_id)) AS ptr_count,ptr.reverse_lookup_name
FROM DOMAIN_PTR_RECORDS AS DPR
LEFT JOIN PTR_RECORDS as PTR on (ptr.id=dpr.ptr_record_id)
GROUP BY ptr.reverse_lookup_name ORDER BY ptr_count DESC

SELECT (count(DNS.nameserver_id)) AS nameserver_count,ns.nameserver
FROM DOMAIN_NAMESERVERS AS DNS
LEFT JOIN nameservers as ns on (dns.nameserver_id=ns.id)
GROUP BY ns.nameserver ORDER BY nameserver_count DESC;
