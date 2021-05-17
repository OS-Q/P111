from platformio.managers.platform import PlatformBase


class P111Platform(PlatformBase):

    def configure_default_packages(self, variables, targets):
        if not variables.get("board"):
            return super(P111Platform, self).configure_default_packages(
                variables, targets)

        build_core = variables.get(
            "board_build.core", self.board_config(variables.get("board")).get(
                "build.core", "arduino"))

        if "arduino" in variables.get(
                "pioframework", []) and build_core != "arduino":
            self.frameworks["arduino"]["package"] = framework_package
            self.packages[framework_package]["optional"] = False
            self.packages["framework-arduino-avr"]["optional"] = True

        upload_protocol = variables.get(
            "upload_protocol",
            self.board_config(variables.get("board")).get(
                "upload.protocol", ""))
        disabled_tool = "tool-micronucleus"
        required_tool = ""

        if upload_protocol == "micronucleus":
            disabled_tool = "tool-avrdude"

        if "fuses" in targets:
            required_tool = "tool-avrdude"

        if required_tool in self.packages:
            self.packages[required_tool]['optional'] = False

        if disabled_tool in self.packages and disabled_tool != required_tool:
            del self.packages[disabled_tool]

        return super(P111Platform, self).configure_default_packages(
            variables, targets)

    def on_run_err(self, line):  # pylint: disable=R0201
        # fix STDERR "flash written" for avrdude
        if "avrdude" in line:
            self.on_run_out(line)
        else:
            PlatformBase.on_run_err(self, line)

    def get_boards(self, id_=None):
        result = PlatformBase.get_boards(self, id_)
        if not result:
            return result
        if id_:
            return self._add_default_debug_tools(result)
        else:
            for key, value in result.items():
                result[key] = self._add_default_debug_tools(result[key])
        return result

    def _add_default_debug_tools(self, board):
        debug = board.manifest.get("debug", {})
        build = board.manifest.get("build", {})
        if "tools" not in debug:
            debug["tools"] = {}

        if debug.get("simavr_target", ""):
            debug["tools"]["simavr"] = {
                "init_cmds": [
                    "define pio_reset_halt_target",
                    "   monitor reset halt",
                    "end",
                    "define pio_reset_run_target",
                    "   monitor reset",
                    "end",
                    "target remote $DEBUG_PORT",
                    "$INIT_BREAK",
                    "$LOAD_CMDS"
                ],
                "port": ":1234",
                "server": {
                    "package": "tool-simavr",
                    "arguments": [
                        "-g",
                        "-m", debug["simavr_target"],
                        "-f", build.get("f_cpu", "")
                    ],
                    "executable": "bin/simavr"
                },
                "onboard": True
            }
        if debug.get("avr-stub", ""):
            speed = debug["avr-stub"]["speed"]
            debug["tools"]["avr-stub"] = {
                "init_cmds": [
                    "define pio_reset_halt_target",
                    "   monitor reset",
                    "end",
                    "define pio_reset_run_target",
                    "end",
                    "set remotetimeout 1",
                    "set serial baud {0}".format(speed),
                    "set remote hardware-breakpoint-limit 8",
                    "set remote hardware-watchpoint-limit 0",
                    "target remote $DEBUG_PORT"
                ],
                "init_break": "",
                "load_cmd": "preload",
                "require_debug_port": True,
                "default": False,
                "onboard": True
            }

        board.manifest["debug"] = debug
        return board