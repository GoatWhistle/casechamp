import { useFormatters, useTranslation } from "@/shared/i18n"
import { formatMetric, type MetricKey, normativeId } from "./metric"

export function useHoverRows(metric: MetricKey, value: number | null, hansen: number | null) {
  const { t } = useTranslation()
  const f = useFormatters()
  const indexRow = {
    key: "hansen",
    label: t("data:metric.hansen"),
    value: hansen === null ? null : formatMetric(hansen, "hansen", f),
  }
  const metricRow = {
    key: metric,
    label: t(`data:metric.${metric}`),
    value: value === null ? null : formatMetric(value, metric, f),
  }
  if (normativeId(metric)) return [metricRow]
  return metric === "hansen" ? [indexRow] : [indexRow, metricRow]
}
