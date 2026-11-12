import time

import numpy as np
from synthetic_traffic.project_dedup import deduplicate_projects
from synthetic_traffic.project_packages import complementary_packages
from synthetic_traffic.surrogate import build_feature_context, features


class SearchCancelled(Exception):
    pass


def prepare_candidates(
    model, network, baseline, pool, package_limit, deadline, cancelled
):
    def check():
        if cancelled and cancelled():
            raise SearchCancelled()
        if time.monotonic() >= deadline:
            raise TimeoutError("Search candidate preparation deadline reached")

    check()
    pool, removed = deduplicate_projects(pool, network)
    if not pool:
        return (
            [],
            np.empty(0),
            {"deduplicated": removed, "invalid_packages": 0, "distinct_projects": 0},
        )
    context = build_feature_context(network, baseline, deadline=deadline, check=check)
    if pool:
        single_features = [
            features(network, baseline, project, context=context) for project in pool
        ]
        single_scores = model.predict(single_features, thread_count=1)
        ranked = [
            pool[index]
            for index in np.argsort(-np.asarray(single_scores), kind="stable")
        ]
    else:
        ranked = []
    check()
    packages, rejected = complementary_packages(
        network, ranked, package_limit, deadline, check
    )
    projects, package_duplicates = deduplicate_projects([*pool, *packages], network)
    check()
    values = (
        model.predict(
            [
                features(network, baseline, project, context=context)
                for project in projects
            ],
            thread_count=1,
        )
        if projects
        else np.empty(0)
    )
    check()
    return (
        projects,
        np.asarray(values),
        {
            "deduplicated": removed + package_duplicates,
            "invalid_packages": rejected,
            "distinct_projects": len(projects),
        },
    )
