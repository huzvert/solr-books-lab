# Sample Solr Queries

Solr admin UI: http://localhost:8983/solr/#/books/query

All queries below hit `http://localhost:8983/solr/books/select`.

## 1. Match all (sanity check)
```
q=*:*&rows=5
```

## 2. Full-text search across multiple fields (edismax)
```
q=quantum machine
defType=edismax
qf=title^3 author^2 description genre
```
`qf` boosts title 3x, author 2x. Results favor docs where the term appears in the title.

## 3. Filter query — narrow to a genre and price range
```
q=*:*
fq=genre:"Science Fiction"
fq=price:[10 TO 30]
```
`fq` is cached separately from `q`, so repeated facet drilldowns are fast.

## 4. Faceted search
```
q=*:*
facet=true
facet.field=genre
facet.field=publisher
facet.mincount=1
rows=0
```
Returns counts per genre/publisher with no documents — ideal for sidebar nav.

## 5. Sorting — newest first, then by rating
```
q=*:*
sort=year desc, rating desc
rows=10
```

## 6. Hit highlighting
```
q=description:freedom
hl=true
hl.fl=description
hl.simple.pre=<mark>
hl.simple.post=</mark>
```

## 7. Range facet (decade buckets)
```
q=*:*
facet=true
facet.range=year
facet.range.start=1950
facet.range.end=2030
facet.range.gap=10
rows=0
```

## 8. Boolean & phrase queries
```
q=title:"Lost Kingdom" AND in_stock:true
```

## 9. Fuzzy search (~2 edit distance)
```
q=author:Smyth~2
```
Matches "Smith", "Smyth", etc.

## 10. Function query — boost by rating
```
q={!boost b=rating}fantasy
defType=lucene
```

## 11. Pagination
```
q=*:*
start=20
rows=10
```

## 12. Group by genre (top 3 per genre)
```
q=*:*
group=true
group.field=genre
group.limit=3
```
