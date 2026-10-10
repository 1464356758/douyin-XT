import importlib.util, unittest
sp=importlib.util.spec_from_file_location("review","scripts/review.py")
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
URL="https://github.com/user-attachments/assets/123456"

def d():
    return {"projects":[{"id":"H30","issue":1,"stage":"IMAGE_PREP","images":[],"videos":[],"last_image_batch":[],"last_video_batch":[],"image_revision":0,"video_revision":0}]}

def ev(body,user="1464356758"):
    return {"action":"created","sender":{"login":user},"issue":{"number":1},"comment":{"body":body}}

class TestWorkflow(unittest.TestCase):
    def test_full_flow(self):
        x=d()
        for cmd in ["/submit-image\n![img]("+URL+")","/approve-image","/submit-video\n[vid]("+URL+")","/approve-video","/published https://www.douyin.com/video/123","/stats views=100 likes=4 shares=2 follows=1"]:
            self.assertTrue(m.apply(x,ev(cmd),"1464356758"))
        self.assertEqual(x["projects"][0]["stage"],"PUBLISHED")
        self.assertEqual(x["projects"][0]["stats"]["views"],100)
    def test_missing_media_rejected(self):
        with self.assertRaises(ValueError):m.apply(d(),ev("/submit-image"),"1464356758")
    def test_no_bypass(self):
        with self.assertRaises(ValueError):m.apply(d(),ev("/approve-image"),"1464356758")
    def test_non_owner(self):
        x=d();self.assertFalse(m.apply(x,ev("/submit-image\n"+URL,"someone"),"1464356758"))
        self.assertEqual(x["projects"][0]["stage"],"IMAGE_PREP")
    def test_rework(self):
        x=d();m.apply(x,ev("/submit-image\n"+URL),"1464356758")
        m.apply(x,ev("/revise-image 脸型不一致"),"1464356758")
        self.assertEqual(x["projects"][0]["stage"],"IMAGE_REWORK")
    def test_external_url(self):
        self.assertFalse(m.allowed("https://evil.example.com/a.png"))
    def test_new_issue(self):
        x=d();import json
        payload=json.dumps({"title":"新作","quote":"新文案","original":"新脚本","kind":"C"},ensure_ascii=False)
        e={"action":"opened","sender":{"login":"1464356758"},"issue":{"number":90,"body":"<!-- FILM_CREATE_V1\n"+payload+"\n-->"}}
        self.assertTrue(m.apply(x,e,"1464356758"))
        self.assertEqual(x["projects"][1]["stage"],"IMAGE_PREP")
if __name__=="__main__":unittest.main()
