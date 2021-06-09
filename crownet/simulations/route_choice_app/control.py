import sys, os

from flowcontrol.crownetcontrol.setup.entrypoints import get_controller_from_args
from flowcontrol.crownetcontrol.setup.vadere import get_scenario_content
from flowcontrol.crownetcontrol.state.state_listener import VadereDefaultStateListener

sys.path.append(os.path.abspath(".."))

from flowcontrol.strategy.controller.dummy_controller import Controller
from flowcontrol.crownetcontrol.traci import constants_vadere as tc
from flowcontrol.utils.misc import get_scenario_file

from shapely import geometry


class DistributeAgentsOverCorridors(Controller):

    def __init__(self):
        super().__init__()
        self.x_center = 15
        self.y_center = 5
        self.radius = 7.5
        self.next_call = 0
        self.counter = 0
        self.target_ids = ["11", "21", "31", "41", "51"]

    def in_circle(self, x, y):
        square_dist = (self.x_center - x) ** 2 + (self.y_center - y) ** 2
        return square_dist <= self.radius ** 2


    def initialize_connection(self, con_manager):
        self.con_manager = con_manager

    def handle_sim_step(self, sim_time, sim_state):

        if self.counter >=5:
            self.counter = 0
        target_id = self.target_ids[self.counter]

        peds1 = self.con_manager.sub_listener["default"].pedestrians
        ids = [p["id"] for p in peds1 if self.in_circle(p["pos"][0],p["pos"][1] )]
        print(f"Set target {target_id}, Ids: {ids}")
        for ped_id in ids:
            self.con_manager.domains.v_person.set_target_list(
                str(ped_id), [target_id]
            )

        self.next_call += 30
        self.con_manager.next_call_at(self.next_call)
        self.counter += 1

    def handle_init(self, sim_time, sim_state):
        print("TikTokController: handle_init")
        self.con_manager.next_call_at(0.0)
        print(sim_state)


if __name__ == "__main__":

    if len(sys.argv) == 1:
        settings = ["--port", "9999", "--host-name", "localhost", "--client-mode", "--start-server", "--controller-type", "PingPong", "--gui-mode"]
    else:
        settings = sys.argv[1:]


    controller = DistributeAgentsOverCorridors()

    scenario_file = get_scenario_file("vadere/scenarios/simplified_default_sequential.scenario")

    sub = VadereDefaultStateListener.with_vars(
        "persons",
        {"pos": tc.VAR_POSITION},
        init_sub=True,
    )

    controller = get_controller_from_args(
        working_dir=os.getcwd(), args=settings, controller= controller
    )

    kwargs = {
        "file_name": scenario_file,
        "file_content": get_scenario_content(scenario_file),
    }
    controller.register_state_listener("default", sub, set_default=True)
    controller.start_controller(**kwargs)

