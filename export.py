#!/usr/bin/env python
import argparse
import requests
import MySQLdb
import pycountry
import sys
import csv

parser = argparse.ArgumentParser()
parser.add_argument("--month", "-m")
args = parser.parse_args()

dbcon = MySQLdb.connect(host="localhost", user="whmcsinvoices", passwd="YOUR_PASSWORD_HERE", db="whmcs")
dbcur = dbcon.cursor(MySQLdb.cursors.DictCursor)

query = """SELECT invoicenum, datepaid, subtotal, total, tax, taxrate,
firstname, lastname, companyname, tblinvoicedata.country
FROM tblinvoices
LEFT JOIN tblclients ON tblclients.id = tblinvoices.userid
INNER JOIN tblinvoicedata ON tblinvoices.id = tblinvoicedata.invoice_id
WHERE datepaid LIKE '2020-%s%%'
ORDER BY invoicenum ASC""" % args.month

dbcur.execute(query)

c = csv.writer(sys.stdout, delimiter='\t');
c.writerow(["Invoice Number", "Payment Date",
"Amount", "VAT", "VAT Rate", "Total", "Total in HRK", "HRK-USD Rate",
"First Name", "Last Name", "Country", "Company Name"])

results = dbcur.fetchall()

get_country_name = lambda x: pycountry.countries.lookup(x).name

exchange_rates = {}

def get_exchange_rate(date):
    rate = exchange_rates.get(date)
    if not rate:
        url = "http://api.hnb.hr/tecajn/v2?valuta=USD&datum-primjene=" + date.isoformat()
        json = requests.get(url).json()
        rate = json[0]["srednji_tecaj"].replace(',', '.')
        rate = float(rate)
        exchange_rates[date] = rate
    return rate

for x in results:
    exchange_rate = get_exchange_rate(x["datepaid"])
    total_in_hrk = round(float(x["total"]) * exchange_rate, 2)

    c.writerow(["'" + x["invoicenum"],
      x["datepaid"], x["subtotal"], x["tax"], x["taxrate"],
      x["total"], total_in_hrk, exchange_rate,
      x["firstname"], x["lastname"],
      get_country_name(x["country"]),
      str(x["companyname"])])

dbcon.close()
