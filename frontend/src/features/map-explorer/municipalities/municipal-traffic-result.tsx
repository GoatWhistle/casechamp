import {
  AssignmentProgress,
  useCancelMunicipalScenario,
  useMunicipalScenarioResult,
} from "@/entities/region"
import { isTrafficJob, type TrafficJob, trafficTerminal } from "@/shared/api/traffic"
import { showTrafficView } from "@/shared/hooks/use-traffic-view"
import { useTranslation } from "@/shared/i18n"
import { Button, Disclosure, Skeleton } from "@/shared/ui"

import { MunicipalLocalEffects } from "./municipal-local-effects"

export function MunicipalTrafficResult({ identifier }: { readonly identifier: string }) {
  const query = useMunicipalScenarioResult(identifier)
  const cancel = useCancelMunicipalScenario()
  const { t } = useTranslation()
  const job = query.data
  if (query.isPending) return <Skeleton lines={3} />
  if (!job || query.isError)
    return <Button onClick={() => void query.refetch()}>{t("map:municipalTraffic.retry")}</Button>
  if (!trafficTerminal(job.status ?? "queued"))
    return (
      <div role="status">
        <p>
          {t("map:municipalTraffic.progress", {
            completed: job.completed ?? 0,
            total: job.total ?? 3,
          })}
        </p>
        <AssignmentProgress value={job.assignment_progress} />
        <Button
          variant="secondary"
          disabled={cancel.isPending || cancel.isSuccess}
          onClick={() => cancel.mutate(identifier)}
        >
          {t("map:municipalTraffic.cancel")}
        </Button>
        {cancel.isError ? <p>{t("map:municipalTraffic.cancelFailed")}</p> : null}
      </div>
    )
  if (job.status !== "completed")
    return (
      <p role="status">
        {t(
          job.status === "cancelled"
            ? "map:municipalTraffic.cancelled"
            : "map:municipalTraffic.failed",
        )}
      </p>
    )
  return isTrafficJob(job) ? (
    <MunicipalTrafficMetrics job={job} />
  ) : (
    <p>{t("map:municipalTraffic.failed")}</p>
  )
}

function MunicipalTrafficMetrics({ job }: { readonly job: TrafficJob }) {
  const { t } = useTranslation()
  const after = job.alternatives?.[0]?.after
  return (
    <div>
      {job.alternatives[0]?.indices?.map((row) => (
        <p key={row.region}>
          {t(
            row.region.startsWith("osm-")
              ? "map:municipalTraffic.localConnectivity"
              : "map:municipalTraffic.regionConnectivity",
            { before: row.before, after: row.after },
          )}
        </p>
      ))}
      <MunicipalLocalEffects identifier={job.id} />
      <Disclosure title={t("map:municipalTraffic.networkEffects")}>
        <p>
          {t("map:municipalTraffic.time", {
            before: job.baseline?.vehicle_hours ?? 0,
            after: after?.vehicle_hours ?? 0,
          })}
        </p>
        <p>
          {t("map:municipalTraffic.lost", {
            before: job.baseline?.unserved_vehicles ?? 0,
            after: after?.unserved_vehicles ?? 0,
          })}
        </p>
        <p>
          {t("map:municipalTraffic.overload", {
            before: job.baseline?.overloaded_edges ?? 0,
            after: after?.overloaded_edges ?? 0,
          })}
        </p>
      </Disclosure>
      <Button
        variant="secondary"
        onClick={() => {
          if (isTrafficJob(job)) showTrafficView(job)
        }}
      >
        {t("map:municipalTraffic.show")}
      </Button>
    </div>
  )
}
