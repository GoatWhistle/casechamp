import type { RegionalIndex } from "@/entities/normative"
import { type MessageKey, useTranslation } from "@/shared/i18n"

const DEFINITION_KEYS: Readonly<Record<string, MessageKey>> = {
  single_reference_point: "normative:indexMeasurementDefinitions.referencePoint",
  stop_pavilion_to_farthest_parcel_boundary_opposite_directions:
    "normative:indexMeasurementDefinitions.stopParcelBoundary",
}

export function IndexMeasurement({ index }: { readonly index: RegionalIndex }) {
  const { t } = useTranslation()
  const required = index.basis?.required_measurement_definition
  if (!required || index.basis?.regulation !== "threshold") return null
  return (
    <>
      <p>
        {t("normative:indexMeasurementRequired", {
          definition: t(DEFINITION_KEYS[required] ?? "normative:indexMeasurementUnknown"),
        })}
      </p>
      {index.run_id ? (
        <p>
          {t("normative:indexMeasurementSaved", {
            definition: t(
              DEFINITION_KEYS[index.measurement_definition] ?? "normative:indexMeasurementUnknown",
            ),
          })}
        </p>
      ) : null}
    </>
  )
}
