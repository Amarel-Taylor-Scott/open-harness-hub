# Synthetic trade-export transaction samples

*dataset* · `dataset/trade-export-samples` · v0.1.0 · experimental

Two synthetic exports:
 - clean: standard laptops to Singapore, EAR99, B-list destination,
   no Entity-list hits, no license required. Expected 0 hits.
 - flagged: Iran destination, Russia onward via HK transshipment,
   Entity List hit, ITAR technical data, deemed-export to H-1B,
   OFAC SDN match on freight forwarder, surveillance tech to MoI,
   dual-use to MEU, cash payment, no end-user cert. Expected many
   critical hits.

| axis | value |
|---|---|
| industry | trade, trade.eccn, trade.itar, trade.sanctions, compliance |
| capability | evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



