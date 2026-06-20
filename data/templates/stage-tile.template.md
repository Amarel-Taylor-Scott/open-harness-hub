<!-- Stage-tile template. Copy is resolved at render time via alias_resolver(stage_id, alias_type, context);
     NEVER hard-code audience labels here. {{alias(id, type)}} is replaced per the active alias pack. -->
## {{alias(stage_id, "label")}}

**{{alias(stage_id, "subtitle")}}**

{{alias(stage_id, "description")}}

<!-- variables: stage_id (canonical), audience, surface; resolved via data/alias-packs/*.yaml -->
