---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Review this new OpenMRS O3 workspace in a frontend module.

```tsx
// allergy-form.workspace.tsx
export default function AllergyForm({ patientUuid, closeWorkspace }) {
  const [reaction, setReaction] = useState('');
  const { t } = useTranslation();

  const handleSave = async () => {
    await openmrsFetch(`/ws/fhir2/R4/AllergyIntolerance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patient: { reference: `Patient/${patientUuid}` }, reaction }),
    });
    closeWorkspace();
  };

  return (
    <Form>
      <TextInput value={reaction} onChange={(e) => setReaction(e.target.value)} />
      <Button onClick={handleSave}>{t('save', 'Save')}</Button>
    </Form>
  );
}

// allergies-widget.tsx (existing, unchanged)
const allergiesUrl = `/ws/fhir2/R4/AllergyIntolerance?patient=${patientUuid}`;
const { data } = useSWR(allergiesUrl, openmrsFetch);
```

Is this good to merge?
