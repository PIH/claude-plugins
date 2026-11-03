---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Review this PR from an outside contributor and draft a ticket comment for it. I want the review summary and the text of a comment for the ticket. Nothing will be posted in this session.

The PR links ticket TRUNK-8888 in the public OpenMRS Jira. There is no PIH ticket for this. The ticket text lives in Jira (assume reading it would work in a real session); the PR metadata and diff are pasted below because gh and the network are unavailable here.

PR: openmrs/openmrs-core#7788, "TRUNK-8888: case insensitive getLocationByName", by an external contributor. CI green.

```diff
--- a/api/src/main/java/org/openmrs/api/db/hibernate/HibernateLocationDAO.java
+++ b/api/src/main/java/org/openmrs/api/db/hibernate/HibernateLocationDAO.java
@@ -60,4 +60,4 @@ public class HibernateLocationDAO implements LocationDAO {
 	public Location getLocationByName(String name) throws DAOException {
-		Criteria criteria = sessionFactory.getCurrentSession().createCriteria(Location.class).add(Restrictions.eq("name", name));
+		Criteria criteria = sessionFactory.getCurrentSession().createCriteria(Location.class).add(Restrictions.eq("name", name).ignoreCase());
 		return (Location) criteria.uniqueResult();
 	}
```
