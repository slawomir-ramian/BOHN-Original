import csv,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"src"))
BASE=ROOT/"experiments"/"11_integrated_system";IDS=["SYS-001","SYS-002","SYS-003","SYS-004","SYS-005","CPU-001","CPU-002","CPU-003","CPU-004","CPU-005"]


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class Stage13Tests(unittest.TestCase):
    def test_pdf_chronology_is_contiguous(self):
        p=ROOT/"inventory"/"source_chronology.csv";p=p if p.exists() else ROOT/"inventory"/"experiments.csv"
        with p.open(encoding="utf-8",newline="") as f:rows=list(csv.DictReader(f))
        self.assertEqual([x["id"] for x in rows[89:99]],IDS)

    def test_historical_and_reported_hashes(self):
        for eid in IDS:
            b=BASE/eid;pr=json.loads((b/"provenance.json").read_text(encoding="utf-8"));name=pr["historical_source_files"][0]
            src=(b/"historical"/name).read_text(encoding="utf-8").rstrip("\n");rep=(b/"historical"/pr["reported_result_file"]).read_text(encoding="utf-8").rstrip("\n")
            self.assertEqual(hashlib.sha256(src.encode()).hexdigest(),pr["historical_source_sha256"][0]);self.assertEqual(hashlib.sha256(rep.encode()).hexdigest(),pr["reported_result_sha256"]);self.assertFalse(pr["historical_code_modified"])

    def test_sys_boundaries_are_not_presented_as_full_runs(self):
        for eid in IDS[:5]:
            p=json.loads((BASE/eid/"provenance.json").read_text(encoding="utf-8"));self.assertEqual(p["source_code_level"],"SOURCE_FRAGMENT_ONLY");self.assertFalse(p["listing_target_code_present"]);self.assertEqual(p["execution_mode"],"AUDIT_REPORTED_RESULT_SOURCE_FRAGMENT")

    def test_cpu_shared_listing_and_source_defect(self):
        hashes=set()
        for eid in IDS[5:]:
            p=json.loads((BASE/eid/"provenance.json").read_text(encoding="utf-8"));self.assertEqual(p["source_code_level"],"FULL_SHARED_LISTING");self.assertTrue(p["listing_target_code_present"]);self.assertEqual(p["source_defect"],"uses_gc_collect_without_importing_gc");hashes.add(p["historical_source_sha256"][0])
        self.assertEqual(len(hashes),1)
        text=(BASE/"CPU-001"/"historical"/"source_from_monograph.py").read_text(encoding="utf-8");self.assertIn("gc.collect()",text);self.assertNotRegex(text,r"(?m)^import gc$")

    @unittest.skipUnless(importlib.util.find_spec("torch"),"PyTorch is installed by setup")
    def test_architecture_contracts(self):
        from bohn_original.integrated_system import PatchEncoder,DeepPatchEncoder,FrozenEncoder,Expert,MetaPermGenerator,TaskRouter,parameter_count
        self.assertEqual(parameter_count(PatchEncoder()),33696);self.assertEqual(parameter_count(DeepPatchEncoder()),66720)
        self.assertEqual(parameter_count(FrozenEncoder()),108736);self.assertEqual(parameter_count(Expert()),4746)
        self.assertEqual(parameter_count(MetaPermGenerator()),553216);self.assertEqual(parameter_count(TaskRouter()),2212)

    def test_parser_and_reference_classification(self):
        r=load(ROOT/"tools"/"run_stage_13.py","r13")
        text="EXPERIMENT 1: Shallow vs Deep Encoder\n"+"\n".join(f"  {e} on {d}: {v}%" for e,x in r.PUB1.items() for d,v in x.items())
        text+="\nEXPERIMENT 2: MoE Multi-Domain Routing\n"
        for d in ["MNIST","Fashion"]:
            text+=f"  {d}: {r.PUB2_ACC[d]}%\n"+"".join(f"    Expert {i}: {v}%\n" for i,v in enumerate(r.PUB2_ROUTE[d]))
        text+=f"  Mixed: {r.PUB2_ACC['Mixed']}%\nEXPERIMENT 3: Cross-Domain Meta-Generator\n"
        for d,v in r.PUB3.items():text+=f"  {d}: Meta-Gen={v[0]}%, Random={v[1]}%, Delta={v[2]:+}%\n"
        text+="EXPERIMENT 4: Partial Unfreeze\n"
        for j,s in enumerate(r.SHOTS):
            text+=f"  --- {s}-shot ---\n"
            for st in r.STRATS:text+=f"    {st}: Fashion={r.PUB4_F[st][j]}%, MNIST={r.PUB4_M[st][j]}%\n"
        text+="EXPERIMENT 5: Few-Shot Scaling\n"+"".join(f"  {s:>5}-shot: {v}%\n" for s,v in r.PUB5.items())
        p=r.parse_cpu(text)
        for eid in IDS[5:]:self.assertEqual(r.compare(eid,p[eid])["status"],"CLOSE_NUMERIC_MATCH")

    def test_red_is_reserved_for_real_errors(self):
        for n in ["SETUP_STAGE_13.ps1","RUN_STAGE_13_SMOKE.ps1","RUN_STAGE_13_FULL.ps1"]:
            t=(ROOT/n).read_text(encoding="utf-8");self.assertNotIn("ForegroundColor Red",t);self.assertIn("ForegroundColor Green",t)


if __name__=="__main__":unittest.main()
