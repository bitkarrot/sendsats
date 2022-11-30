# sendsats

An API for getting QR codes and Bolt11 Invoices from Lightning Addresses. Share anywhere; as a link for tips on a twitter profile, or via messenger apps.

Uses LNBits-legend as a backend.

This is a Work in Progress!

Example Use:

replace me@mydomain.com with your lightning address

- https://sendsats.to/me@mydomain.com
will return a scannable Lightning QR Code for any valid Lightning Address.
currently it defaults to 10 sats, and is in PNG format

- https://sendsats.to/tip/me@mydomain.com/amt/1000
will return a scannable Lightning QRCode for 1000 sats in PNG

- https://sendsats.to/svg/me@mydomain.com
will return a SVG - XML format QR code in json format that can be embedded into other content.

- https://sendsats.to/bolt11/me@mydomain.com
will return a bolt11 invoice in json format.

---

**Documentation:** <a href="https://sendsats.to/docs" target="_blank">https://sendsats.to/docs</a>

**Source Code:** <a href="https://github.com/bitkarrot/sendsats" target="_blank"> https://github.com/bitkarrot/sendsats </a>

---

## Deploy your own copy on Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fbitkarrot%2Fsendsats) 


**Live Demo:** <a href="https://sendsats.to">https://sendsats.to</a>


This is a work in progress

## TODO:

- QR codes with text indicators
- pytest
- pydantic
- docs

