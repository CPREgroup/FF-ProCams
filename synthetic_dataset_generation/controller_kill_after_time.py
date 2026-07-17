import argparse
import datetime
import subprocess
import time
import psutil
import render_config as cfg

# Default runtime configuration. Values are loaded from render_defaults.yaml.
DEFAULT_BLENDER_EXECUTABLE = cfg.get_default("controller_blender_executable")
DEFAULT_BLEND_FILE = cfg.get_default("controller_blend_file")
DEFAULT_BLENDER_SCRIPT = cfg.get_default("controller_script")
DEFAULT_OBJ_FOLDER = cfg.get_default("controller_obj_folder")
DEFAULT_TEXTURES_ROOT = cfg.get_default("controller_textures_root")
DEFAULT_SAMPLES = cfg.get_default("controller_samples")
DEFAULT_RADIUS = cfg.get_default("controller_radius")
DEFAULT_RUN_DURATION_SECONDS = cfg.get_default("controller_run_duration_seconds")
RESTART_DELAY_SECONDS = cfg.get_default("controller_restart_delay_seconds")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a Blender rendering script and restart it after a fixed timeout."
    )
    parser.add_argument("--start", type=int, required=True, help="Inclusive texture-folder start index.")
    parser.add_argument("--end", type=int, required=True, help="Exclusive texture-folder end index.")
    parser.add_argument("--blender", default=DEFAULT_BLENDER_EXECUTABLE, help="Path to the Blender executable.")
    parser.add_argument("--blend-file", default=DEFAULT_BLEND_FILE, help="Path to the base .blend scene file.")
    parser.add_argument("--script", default=DEFAULT_BLENDER_SCRIPT, help="Path to the Blender Python script.")
    parser.add_argument("--obj-folder", default=DEFAULT_OBJ_FOLDER, help="Directory containing .obj meshes.")
    parser.add_argument("--textures-root", default=DEFAULT_TEXTURES_ROOT, help="Root directory containing texture metadata.")
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES, help="Cycles sample count passed to Blender.")
    parser.add_argument("--radius", type=float, default=DEFAULT_RADIUS, help="Camera orbit radius passed to Blender.")
    parser.add_argument(
        "--run-duration-seconds",
        type=int,
        default=DEFAULT_RUN_DURATION_SECONDS,
        help="Maximum Blender runtime before the process is restarted.",
    )
    return parser.parse_args()


def start_blender_process(args):
    cmd = [
        args.blender,
        "-b", args.blend_file,
        "-P", args.script,
        "--",
        f"--obj_folder={args.obj_folder}",
        f"--textures_root={args.textures_root}",
        f"--samples={args.samples}",
        f"--radius={args.radius}",
        f"--start={args.start}",
        f"--end={args.end}",
    ]
    print(f"[{datetime.datetime.now()}] Starting Blender")
    return subprocess.Popen(cmd)


def kill_process(proc):
    print(f"[{datetime.datetime.now()}] Timeout reached; killing Blender process PID={proc.pid}")
    process = psutil.Process(proc.pid)
    for child in process.children(recursive=True):
        child.kill()
    process.kill()


def main_loop(args):
    proc = None
    try:
        while True:
            proc = start_blender_process(args)
            start_time = time.time()

            while True:
                if proc.poll() is not None:
                    print(f"[{datetime.datetime.now()}] Blender exited normally; controller is stopping")
                    return

                elapsed = time.time() - start_time
                if elapsed > args.run_duration_seconds:
                    kill_process(proc)
                    print(f"[{datetime.datetime.now()}] Restarting Blender after timeout")
                    break

                time.sleep(RESTART_DELAY_SECONDS)

            print(f"[{datetime.datetime.now()}] Waiting {RESTART_DELAY_SECONDS} seconds before restart")
            time.sleep(RESTART_DELAY_SECONDS)
    except KeyboardInterrupt:
        print("Controller interrupted.")
        if proc is not None and proc.poll() is None:
            proc.terminate()


if __name__ == "__main__":
    main_loop(parse_args())
