import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ShieldAlert } from "lucide-react";

import { apiRequest } from "../../lib/api/client";
import { ConfirmButton, DataState, MutationError, PageHeader, StatusBadge } from "./components";
import type { Agent, Fleet } from "./types";

export function EmergencyPage() {
  const client = useQueryClient();
  const fleets = useQuery({
    queryKey: ["fleets"],
    queryFn: () => apiRequest<Fleet[]>("fleets?limit=500"),
  });
  const agents = useQuery({
    queryKey: ["agents"],
    queryFn: () => apiRequest<Agent[]>("agents?limit=500"),
  });
  const fleetAction = useMutation({
    mutationFn: ({ id, action }: { id: string; action: string }) =>
      apiRequest(`fleets/${id}/${action}`, { method: "POST" }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["fleets"] }),
  });
  const agentAction = useMutation({
    mutationFn: ({ id, action }: { id: string; action: string }) =>
      apiRequest(`agents/${id}/${action}`, { method: "POST" }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["agents"] }),
  });
  const stopped = fleets.data?.filter((item) => item.status !== "enabled").length ?? 0;

  return (
    <div className="operator-page">
      <PageHeader
        eyebrow="Immediate intervention"
        title="Emergency control center"
        description="Stop governed execution at fleet or individual agent scope."
      />
      <div className={`emergency-banner ${stopped ? "active" : ""}`} role="status">
        <ShieldAlert size={24} />
        <div>
          <strong>{stopped ? `${stopped} fleet controls active` : "All fleets operational"}</strong>
          <span>
            Every stop is enforced by the financial-action gateway and recorded in the immutable
            audit trail.
          </span>
        </div>
      </div>
      <MutationError error={fleetAction.error ?? agentAction.error ?? null} />
      <div className="operator-grid two-column">
        <section className="panel operator-panel">
          <div className="panel-header">
            <h2>Fleet controls</h2>
          </div>
          <DataState loading={fleets.isLoading} error={fleets.error} empty={!fleets.data?.length}>
            <div className="control-list">
              {fleets.data?.map((fleet) => (
                <article key={fleet.id}>
                  <div>
                    <strong>{fleet.name}</strong>
                    <StatusBadge value={fleet.status} />
                  </div>
                  <div className="row-actions">
                    <ConfirmButton
                      className="danger-button"
                      message={`Emergency stop ${fleet.name}?`}
                      onConfirm={() =>
                        fleetAction.mutate({ id: fleet.id, action: "emergency-stop" })
                      }
                    >
                      Stop fleet
                    </ConfirmButton>
                    <ConfirmButton
                      message={`Recover ${fleet.name}?`}
                      onConfirm={() => fleetAction.mutate({ id: fleet.id, action: "enable" })}
                    >
                      Recover
                    </ConfirmButton>
                  </div>
                </article>
              ))}
            </div>
          </DataState>
        </section>
        <section className="panel operator-panel">
          <div className="panel-header">
            <h2>Agent controls</h2>
          </div>
          <DataState loading={agents.isLoading} error={agents.error} empty={!agents.data?.length}>
            <div className="control-list">
              {agents.data?.map((agent) => (
                <article key={agent.id}>
                  <div>
                    <strong>{agent.name}</strong>
                    <StatusBadge value={agent.status} />
                  </div>
                  <div className="row-actions">
                    <ConfirmButton
                      className="danger-button"
                      message={`Disable ${agent.name}?`}
                      onConfirm={() => agentAction.mutate({ id: agent.id, action: "disable" })}
                    >
                      Stop agent
                    </ConfirmButton>
                    <ConfirmButton
                      message={`Enable ${agent.name}?`}
                      onConfirm={() => agentAction.mutate({ id: agent.id, action: "enable" })}
                    >
                      Recover
                    </ConfirmButton>
                  </div>
                </article>
              ))}
            </div>
          </DataState>
        </section>
      </div>
    </div>
  );
}
