# Sample Solr Queries

Solr admin UI: http://localhost:8983/solr/#/products/query

All queries below hit `http://localhost:8983/solr/products/select`.

## 1. Match all (sanity check)
```
q=*:*&rows=5
```

## 2. Full-text search across multiple fields (edismax)
```
q=running shoes
defType=edismax
qf=title^3 brand_text^2 description category
```
Title is boosted 3x and brand_text 2x, so a result whose title contains
"running shoes" beats a result that only mentions running in its description.

## 3. Filter query — narrow to a category and price range
```
q=*:*
fq=category:"Electronics"
fq=price:[10 TO 50]
```
`fq` is cached separately from `q`, so repeated facet drilldowns are fast.

## 4. Faceted search
```
q=*:*
facet=true
facet.field=category
facet.field=brand
facet.mincount=1
rows=0
```
Returns counts per category and brand without any documents — exactly what
the sidebar needs.

## 5. Sorting — top-rated, then most reviewed
```
q=*:*
sort=rating desc, num_reviews desc
rows=10
```

## 6. Hit highlighting
```
q=description:wireless
hl=true
hl.fl=description
hl.simple.pre=<mark>
hl.simple.post=</mark>
```

## 7. Range facet (price buckets)
```
q=*:*
facet=true
facet.range=price
facet.range.start=0
facet.range.end=500
facet.range.gap=50
rows=0
```

## 8. Boolean & phrase queries
```
q=title:"running shoes" AND in_stock:true
```

## 9. Fuzzy search (~2 edit distance)
```
q=brand_text:Adidaz~2
```
Matches `adidas`, even though it's misspelled.

## 10. Function query — boost by rating
```
q={!boost b=rating}category:Electronics
defType=lucene
```

## 11. Pagination
```
q=*:*
start=100
rows=10
```

## 12. Group by category (top 2 per category)
```
q=*:*
group=true
group.field=category
group.limit=2
```
