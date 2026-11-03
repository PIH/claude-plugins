---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Review this PR from an outside contributor. Note: gh, Jira and network tools are unavailable in this session, and no repository is checked out. Everything you need is pasted below as the provided data. Work from it and do not try to fetch anything. The PR links ticket TRUNK-8888, whose text is: \"LocationService.getLocationByName is case sensitive; make it case insensitive for consistency with other name lookups.\" There is no PIH ticket for this. I have not said anything about whether the ticket contains patient data. Nothing will be posted in this session.

PR: openmrs/openmrs-core#7788, \"TRUNK-8888: case insensitive getLocationByName\", by an external contributor. CI green.

```diff
--- a/api/src/main/java/org/openmrs/api/db/hibernate/HibernateLocationDAO.java
+++ b/api/src/main/java/org/openmrs/api/db/hibernate/HibernateLocationDAO.java
@@ -60,4 +60,4 @@ public class HibernateLocationDAO implements LocationDAO {
 	public Location getLocationByName(String name) throws DAOException {
-		Criteria criteria = sessionFactory.getCurrentSession().createCriteria(Location.class).add(Restrictions.eq(\"name\", name));
+		Criteria criteria = sessionFactory.getCurrentSession().createCriteria(Location.class).add(Restrictions.eq(\"name\", name).ignoreCase());
 		return (Location) criteria.uniqueResult();
 	}
```
