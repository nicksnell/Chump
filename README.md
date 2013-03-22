# Chump - Utility HTML Parser


---

### Notes

We are only interested in a handful of tags, namely;
- div
- header
- footer
- nav
- section
- aside

and we are only interested in these if they have class edit-local/edit-global
though we are interested in the other attributes potentially.

We can be sure that no none tag data will be specified inside our editable 
regions, only safe HTML can go there. Outside of the editable regions though 
it's fair game.

The parser needs to return the following information;

- Regions - a dictionary of regions keyed by the regions ID
	- Region
		: properties
		- id
		- attributes
		- content
		- outer - location of the region including the tag
		- inner - location of the region excluding the tag

Putting the regions in place is going to be difficult we need to remember each
section within the string. Regions can't overlap so we can simply solve the 
problem by replacing in reverse order.
