import unittest
import match_goals

class StrategyTests(unittest.TestCase):

    def setup(self):
        self.odds_file = "data/xds/historic/BASIC/28522440/1.138129751"
        self.data = match_goals.read_odds_file(self.odds_file)
        self.events = match_goals.get_events(self.data)

    def test_match_start(self):
        self.setup()
        start_data = match_goals.match_start_data(self.events)
        self.assertTrue(len(self.data)==314)        
        self.assertTrue(start_data["clk"]=="5830395944")
        self.assertTrue(match_goals.get_ids(start_data)[0]==58805)
        start_odds = {"op":"mcm","clk":"5830387585","pt":1515142526796,"mc":[{"id":"1.138129751","rc":[{"ltp":3.6,"id":58805},{"ltp":3.6,"id":6480414}]}]}
        self.assertTrue(match_goals.get_draw_odds_1_min_before_start(self.data)==3.6)

    def test_goals(self):
        self.setup()
        goal_data = match_goals.match_goal_data(self.events)
        self.assertTrue(match_goals._get_odds_before_goal(goal_data[0], self.data)==\
[{u'ltp': 3.25, u'id': 58805}, {u'ltp': 2.2, u'id': 3862627}, {u'ltp': 4.2, u'id': 6480414}])
        self.assertTrue(match_goals._prettify_odds([{u'ltp': 1.89, u'id': 6480414}, {u'ltp': 4.8, u'id': 3862627}])==\
        {6480414: 1.89, 3862627: 4.8})
        self.assertTrue(match_goals.get_goals(goal_data, self.data)[0]==\
            {3862627: 0, 6480414: 1, 'clk': u'5830553541'})

if __name__ == "__main__":
    unittest.main()
