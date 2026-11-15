type Nutrition = {
  calories?: number | null;
  carbs_g?: number | null;
  sodium_mg?: number | null;
  sugar_g?: number | null;
  sat_fat_g?: number | null;
  potassium_mg?: number | null;
};

function amount(value: number | null | undefined, unit: string) {
  return value === null || value === undefined ? "Not available" : `${value} ${unit}`;
}

// The label's fact rows, shared by Scan and Cart so both read the same.
// Calories and carbs are display only (they never change the status) and show only when the API sends them.
export default function NutritionFacts({ facts }: { facts: Nutrition }) {
  return (
    <dl className="facts">
      {facts.calories !== undefined && (
        <div>
          <dt>Calories</dt>
          <dd>{facts.calories === null ? "Not available" : facts.calories}</dd>
        </div>
      )}
      <div>
        <dt>Sodium</dt>
        <dd>{amount(facts.sodium_mg, "mg")}</dd>
      </div>
      {facts.carbs_g !== undefined && (
        <div>
          <dt>Total carbs</dt>
          <dd>{amount(facts.carbs_g, "g")}</dd>
        </div>
      )}
      <div>
        <dt>Sugar</dt>
        <dd>{amount(facts.sugar_g, "g")}</dd>
      </div>
      <div>
        <dt>Saturated fat</dt>
        <dd>{amount(facts.sat_fat_g, "g")}</dd>
      </div>
      <div>
        <dt>Potassium</dt>
        <dd>{amount(facts.potassium_mg, "mg")}</dd>
      </div>
    </dl>
  );
}
