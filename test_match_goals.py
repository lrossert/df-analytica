import unittest
import match_goals

class StrategyTests(unittest.TestCase):

    def setup(self):
        self.odds_file = "data/xds/historic/BASIC/28522440/1.138129751"
        self.match = match_goals.Match(self.odds_file)

    def test_match_start(self):
        self.setup()
        self.assertTrue(len(self.match.data)==314)        
        self.assertTrue(self.match.start_data["clk"]=="5830395944")
        self.assertTrue(self.match.get_ids()[0]==58805)
        start_odds = {"op":"mcm","clk":"5830387585","pt":1515142526796,"mc":[{"id":"1.138129751","rc":[{"ltp":3.6,"id":58805},{"ltp":3.6,"id":6480414}]}]}
        self.assertTrue(self.match.match_start_odds==3.6)

    def test_goals(self):
        self.setup()
        goal_data = self.match.goal_data
        self.assertTrue(self.match.get_goals()[0]==\
            {3862627: 0, 6480414: 1, 'clk': u'5830553541'})

if __name__ == "__main__":
    unittest.main()
