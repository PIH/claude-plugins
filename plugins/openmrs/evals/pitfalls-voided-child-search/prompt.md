---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Review this HQL patient search I added to a module's DAO.

```java
public List<Patient> findByIdentifierFragment(String fragment) {
    return sessionFactory.getCurrentSession().createQuery(
        "select distinct p from Patient p join p.identifiers pi " +
        "where p.voided = false and pi.identifier like :frag", Patient.class)
        .setParameter("frag", "%" + fragment + "%")
        .list();
}
```

Anything you would change before I open the PR?
