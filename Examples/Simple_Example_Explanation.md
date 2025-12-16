

### **Entity 1: Alice**
```xml
<rdf:Description rdf:about="http://example.org/Alice">
    <rdfs:label>Alice</rdfs:label>        <!-- Alice's name -->
    <ex:age>25</ex:age>                   <!-- Alice's age -->
    <ex:knows rdf:resource="http://example.org/Bob"/>  <!-- Alice knows Bob -->
</rdf:Description>
```

### **Entity 2: Bob**
```xml
<rdf:Description rdf:about="http://example.org/Bob">
    <rdfs:label>Bob</rdfs:label>          <!-- Bob's name -->
    <ex:age>30</ex:age>                   <!-- Bob's age -->
    <ex:worksAt rdf:resource="http://example.org/Company"/>  <!-- Bob works at Company -->
</rdf:Description>
```

### **Entity 3: Company**
```xml
<rdf:Description rdf:about="http://example.org/Company">
    <rdfs:label>TechCorp</rdfs:label>     <!-- Company name -->
    <ex:hasEmployee rdf:resource="http://example.org/Bob"/>  <!-- Company has Bob as employee -->
</rdf:Description>
```

---

## 🎯 RDF Triples (Subject → Predicate → Object):

### **Triple 1:**
- **Subject**: Alice
- **Predicate**: has name
- **Object**: "Alice" (literal)

### **Triple 2:**
- **Subject**: Alice  
- **Predicate**: has age
- **Object**: 25 (literal)

### **Triple 3:**
- **Subject**: Alice
- **Predicate**: knows
- **Object**: Bob (resource)

### **Triple 4:**
- **Subject**: Bob
- **Predicate**: has name
- **Object**: "Bob" (literal)

### **Triple 5:**
- **Subject**: Bob
- **Predicate**: has age
- **Object**: 30 (literal)

### **Triple 6:**
- **Subject**: Bob
- **Predicate**: works at
- **Object**: Company (resource)

### **Triple 7:**
- **Subject**: Company
- **Predicate**: has name
- **Object**: "TechCorp" (literal)

### **Triple 8:**
- **Subject**: Company
- **Predicate**: has employee
- **Object**: Bob (resource)

---

## 🔗 How It Becomes a Graph:

### **Nodes (3 total):**
1. **Alice** - with properties: name="Alice", age=25
2. **Bob** - with properties: name="Bob", age=30  
3. **Company** - with properties: name="TechCorp"

### **Edges (3 total):**
1. **Alice** → **Bob** (knows)
2. **Bob** → **Company** (works at)
3. **Company** → **Bob** (has employee)

---

## 📊 Visual Representation:

```
Alice (25) ──knows──→ Bob (30) ──works at──→ Company (TechCorp)
                              ←──has employee───┘
```

---

## 🧪 Test This Example:

1. **Upload** `simple_example.xml` to your app
2. **Expected Result**: 3 nodes, 3 edges
3. **Perfect for understanding** how RDF works

---

## 💡 Why This Example is Perfect:

- **Only 3 entities** - easy to count
- **Only 3 relationships** - simple to visualize
- **Clear structure** - obvious what should happen
- **No complex types** - just basic resources and literals
- **Perfect for debugging** - you can see exactly what's working

This simple example will help you understand exactly how RDF triples become nodes and edges in your knowledge graph! 🎯
