
import tempfile

from src.acpc.runtime import ACPCNode, Delta, NodeConfig


def test_idempotent_duplicate_event():
    with tempfile.TemporaryDirectory() as d:
        n = ACPCNode(NodeConfig("A", d, ("p1",)))
        e = n.emit("p1", Delta("set", ("pv", "kw"), 12))
        n.receive(e)
        n.receive(e)
        assert n.state("p1")["pv"]["kw"] == 12
        assert n.vector("p1") == {"A": 1}


def test_out_of_order_buffering_and_ordering():
    with tempfile.TemporaryDirectory() as da, tempfile.TemporaryDirectory() as db:
        a = ACPCNode(NodeConfig("A", da, ("p1",)))
        b = ACPCNode(NodeConfig("B", db, ("p1",)))
        e1 = a.emit("p1", Delta("set", ("x",), 1))
        e2 = a.emit("p1", Delta("set", ("x",), 2))
        b.receive(e2)
        assert b.state("p1") == {}
        b.receive(e1)
        assert b.state("p1")["x"] == 2
        assert b.vector("p1")["A"] == 2


def test_snapshot_restore_replay():
    with tempfile.TemporaryDirectory() as d:
        n = ACPCNode(NodeConfig("A", d, ("p1",)))
        n.emit("p1", Delta("set", ("meter", "kwh"), 100))
        n.snapshot("p1")
        n.emit("p1", Delta("increment", ("meter", "kwh"), 5))

        restored = ACPCNode(NodeConfig("A", d, ("p1",)))
        restored.restore("p1")
        assert restored.state("p1")["meter"]["kwh"] == 105


def test_deterministic_conflict_resolution():
    with tempfile.TemporaryDirectory() as da, tempfile.TemporaryDirectory() as db, tempfile.TemporaryDirectory() as dc:
        a = ACPCNode(NodeConfig("A", da, ("p1",)))
        b = ACPCNode(NodeConfig("B", db, ("p1",)))
        c1 = ACPCNode(NodeConfig("C1", dc+"/c1", ("p1",)))
        c2 = ACPCNode(NodeConfig("C2", dc+"/c2", ("p1",)))

        ea = a.emit("p1", Delta("set", ("asset", "mode"), "charge"))
        eb = b.emit("p1", Delta("set", ("asset", "mode"), "discharge"))

        c1.receive(ea); c1.receive(eb)
        c2.receive(eb); c2.receive(ea)

        assert c1.state("p1") == c2.state("p1")
