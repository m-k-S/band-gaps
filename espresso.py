import subprocess
import time
from config import bandgapConfig

def extract_latest_energy_and_cpu_time(file):
    total_energy_line = None
    cpu_time_line = None
    convergence = None

    for line in file:
        if "total energy" in line and "Ry" in line:
            total_energy_line = line.strip()
        if "total cpu time spent up to now is" in line:
            cpu_time_line = line.strip()
        if "convergence has been achieved" in line:
            convergence = line.strip()
    
    total_energy = total_energy_line.split('=')[1].strip().split("Ry")[0].strip() if total_energy_line else None
    cpu_time = cpu_time_line.split('is')[1].strip() if cpu_time_line else None
    convergence = convergence if convergence else None
    
    return total_energy, cpu_time, convergence

def run_pwscf(
        num_cores,
        rundir,
        input_file,
        output_file,
    ):
    command = f"mpirun -np {num_cores} pw.x -inp {rundir}/{input_file} > {rundir}/{output_file}"
    # Start the command
    process = subprocess.Popen(command, shell=True)
    
    # Open the outfile for reading
    time.sleep(5)
    with open(f"{rundir}/{output_file}", 'r') as outfile:
        # Check if the process is still running
        current_energy = 0
        while process.poll() is None:
            # Read the latest output from the outfile
            total_energy, cpu_time, _ = extract_latest_energy_and_cpu_time(outfile)
            if total_energy:
                energy_diff = abs(float(current_energy) - float(total_energy))
                current_energy = total_energy
                print(
                    f"""Total Energy: {total_energy} Ry
                    Energy Difference: {energy_diff} Ry
                    CPU Time: {cpu_time} seconds""",
                    end="\r"
                )
            # Sleep a bit before checking again
            time.sleep(5)

        # one more time when process finishes        
        total_energy, cpu_time, convergence = extract_latest_energy_and_cpu_time(outfile)
        
        return_code = process.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, command)
        return total_energy, cpu_time, convergence

def create_qe_file(
        params,
        rundir,
        output_file,
    ):
    for card, vals in params.items():
        input = f"&{card.upper()}\n"
        for key, val in vals.items():
            if val:
                input += f"    {key} = {val},\n"
        input += f"/"

    with open(f"{rundir}/{output_file}", 'w') as outfile:
        outfile.write(input)

def run_bands(
        rundir,
        input_file,
        output_file,
    ):
    command = f"bands.x < {rundir}/{input_file} > {rundir}/{output_file}"
    # Start the command
    process = subprocess.Popen(command, shell=True)
    
    # Open the outfile for reading
    time.sleep(5)
    with open(f"{rundir}/{output_file}", 'r') as outfile:
        # Check if the process is still running
        while process.poll() is None:
            # Read the latest output from the outfile
            output = outfile.read()
            if output:
                print(output, end='')
            # Sleep a bit before checking again
            time.sleep(0.5)
        
        # Process has finished, read any remaining output
        output = outfile.read()
        if output:
            print(output, end='')
        
        return_code = process.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, command)

def run_dos(
        rundir,
        input_file,
        output_file,
    ):
    command = f"dos.x < {rundir}/{input_file} > {rundir}/{output_file}"
    # Start the command
    process = subprocess.Popen(command, shell=True)
    
    # Open the outfile for reading
    time.sleep(5)
    with open(f"{rundir}/{output_file}", 'r') as outfile:
        # Check if the process is still running
        while process.poll() is None:
            # Read the latest output from the outfile
            output = outfile.read()
            if output:
                print(output, end='')
            # Sleep a bit before checking again
            time.sleep(0.5)
        
        # Process has finished, read any remaining output
        output = outfile.read()
        if output:
            print(output, end='')
        
        return_code = process.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, command)

def run_pdos(
        rundir,
        input_file,
        output_file,
    ):
    command = f"projwfc.x < {rundir}/{input_file} > {rundir}/{output_file}"
    # Start the command
    process = subprocess.Popen(command, shell=True)
    
    # Open the outfile for reading
    time.sleep(5)
    with open(f"{rundir}/{output_file}", 'r') as outfile:
        # Check if the process is still running
        while process.poll() is None:
            # Read the latest output from the outfile
            output = outfile.read()
            if output:
                print(output, end='')
            # Sleep a bit before checking again
            time.sleep(0.5)
        
        # Process has finished, read any remaining output
        output = outfile.read()
        if output:
            print(output, end='')
        
        return_code = process.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, command)
