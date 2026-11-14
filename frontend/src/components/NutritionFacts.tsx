type Nutrition = {
  sodium_mg?: number | null;
  sugar_g?: number | null;
  sat_fat_g?: number | null;
  potassium_mg?: number | null;
};

function amount(value: number | null | undefined, unit: string) {
  return value === null || value === undefined ? "Not available" : `${value} ${unit}`;
}

// The label's fact rows, shared by Scan and Cart so both read the same.
export default function NutritionFacts({ facts }: { facts: Nutrition }) {
  return (
    <dl className="facts">
      <div>
        <dt>Sodium</dt>
        <dd>{amount(facts.sodium_mg, "mg")}</dd>
      </div>
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
