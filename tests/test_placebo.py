from skill_placebo.placebo import assign_buckets


def test_assign_buckets_greedy_within_tolerance():
    L = {"karpathy": 2345, "planning": 2646, "mattpocock": 4106, "superpowers": 6020, "adhd": 7291,
         "ponytail": 7874, "compound": 7943, "caveman": 10043, "agent-skills": 10973}
    b = assign_buckets(L)
    assert b == [["karpathy", "planning"], ["mattpocock"], ["superpowers"], ["adhd", "ponytail", "compound"],
                 ["caveman", "agent-skills"]]
    for bucket in b:
        mean = sum(L[m] for m in bucket) / len(bucket)
        assert all(abs(mean / L[m] - 1) <= 0.10 for m in bucket)


def test_assign_buckets_is_order_independent():
    L = {"a": 100, "b": 105, "c": 300}
    assert assign_buckets(L) == assign_buckets(dict(reversed(list(L.items()))))
