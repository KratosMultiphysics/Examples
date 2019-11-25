import numpy, math, os
import matplotlib.pyplot as plt

plt.rcParams.update({'font.size': 22})

def read_jovic94(table_id):
    with open("jovic94.dat", "r") as file_input:
        lines = file_input.readlines()

    start_line = -1
    table_lines = []

    for line in lines:
        if line[:5] == "Table":
            if int(line[6:line.find(":")]) == table_id:
                start_line += 1
                print("Reading " + line[:-1])

        if line == "\n":
            start_line = -1

        if (start_line <= 2 and start_line > -1):
            start_line += 1
            continue

        if start_line > -1:
            table_lines.append(line[:-1])

    return numpy.loadtxt(table_lines)


def plot_jovic_velocity(table_id):
    x_h_values = [0, 0, 0, 0, -3.12, 4.0, 6.0, 10.0, 15.0, 19.0]
    i = table_id
    data = read_jovic94(i)
    plt.plot(
        data[:, 1] / 7.72,
        data[:, 0] / 9.8,
        "-",
        label=r"Jovic $et al.$ $\frac{x}{h}=%0.2f$" % x_h_values[i - 1])


def plot_kratos_velocity(filename, y_offset):
    ref_velocity = 7.72
    data = numpy.loadtxt(filename, delimiter=',')
    plt.plot(
        data[:, 4] / ref_velocity, (data[:, 2] - y_offset) / 9.8e-3,
        "--",
        label=r"RANSApplication $k-\epsilon$ high $Re$")

def plot_jovic_turbulent_kinetic_energy(table_id):
    x_h_values = [0, 0, 0, 0, -3.12, 4.0, 6.0, 10.0, 15.0, 19.0]
    i = table_id
    data = read_jovic94(i)

    tke = 0.5 * (data[:, 3] + data[:, 4])

    plt.plot(
        tke / 7.72**2,
        data[:, 0] / 9.8,
        "-",
        label=r"Jovic $et al.$ $\frac{x}{h}=%0.2f$" % x_h_values[i - 1])

def plot_kratos_turbulent_kinetic_energy(filename, y_offset):
    ref_velocity = 7.72
    data = numpy.loadtxt(filename, delimiter=',')
    plt.plot(
        data[:, 7] / ref_velocity**2, (data[:, 2] - y_offset) / 9.8e-3,
        "--",
        label=r"RANSApplication $k-\epsilon$ high $Re$")

if __name__ == "__main__":
    plt.figure(figsize=(12, 9))
    plt.title(
        r"Backward Facing Step Velocity Fluctuation at $x/h=-3.12$ with $Re_h=5000$"
    )
    plot_jovic_velocity(5)
    plot_kratos_velocity("line_outputs/x=-3.12h_1.csv", 9.8e-3)
    plt.xlabel(r"$u/u_\infty$")
    plt.ylabel(r"y/h")
    plt.legend(loc="upper left")
    plt.grid(True)
    plt.savefig(
        'plots/velocity_x=-3.12h.png', bbox_inches='tight')

    plt.figure(figsize=(12, 9))
    plt.title(
        r"Backward Facing Step Velocity Fluctuation at $x/h=4.00$ with $Re_h=5000$"
    )
    plot_jovic_velocity(6)
    plot_kratos_velocity("line_outputs/x=4h_1.csv", 0.0)
    plt.xlabel(r"$u/u_\infty$")
    plt.ylabel(r"y/h")
    plt.legend(loc="upper left")
    plt.grid(True)
    plt.savefig(
        'plots/velocity_x=4h.png', bbox_inches='tight')

    plt.figure(figsize=(12, 9))
    plt.title(
        r"Backward Facing Step Velocity Fluctuation at $x/h=6.00$ with $Re_h=5000$"
    )
    plot_jovic_velocity(7)
    plot_kratos_velocity("line_outputs/x=6h_1.csv", 0.0)
    plt.xlabel(r"$u/u_\infty$")
    plt.ylabel(r"y/h")
    plt.legend(loc="upper left")
    plt.grid(True)
    plt.savefig(
        'plots/velocity_x=6h.png', bbox_inches='tight')

    plt.figure(figsize=(12, 9))
    plt.title(
        r"Backward Facing Step $k$ Fluctuation at $x/h=6.00$ with $Re_h=5000$"
    )
    plot_jovic_turbulent_kinetic_energy(5)
    plot_kratos_turbulent_kinetic_energy("line_outputs/x=-3.12h_1.csv", 9.8e-3)
    plt.xlabel(r"$k/u_\infty^2$")
    plt.ylabel(r"y/h")
    plt.legend(loc="upper left")
    plt.grid(True)
    plt.savefig(
        'plots/turbulent_kinetic_energy_x=-3.12h.png', bbox_inches='tight')

    plt.figure(figsize=(12, 9))
    plt.title(
        r"Backward Facing Step $k$ Fluctuation at $x/h=6.00$ with $Re_h=5000$"
    )
    plot_jovic_turbulent_kinetic_energy(6)
    plot_kratos_turbulent_kinetic_energy("line_outputs/x=4h_1.csv", 0.0)
    plt.xlabel(r"$k/u_\infty^2$")
    plt.ylabel(r"y/h")
    plt.legend(loc="upper left")
    plt.grid(True)
    plt.savefig(
        'plots/turbulent_kinetic_energy_x=4h.png', bbox_inches='tight')

    plt.figure(figsize=(12, 9))
    plt.title(
        r"Backward Facing Step $k$ Fluctuation at $x/h=6.00$ with $Re_h=5000$"
    )
    plot_jovic_turbulent_kinetic_energy(7)
    plot_kratos_turbulent_kinetic_energy("line_outputs/x=6h_1.csv", 0.0)
    plt.xlabel(r"$k/u_\infty^2$")
    plt.ylabel(r"y/h")
    plt.legend(loc="upper left")
    plt.grid(True)
    plt.savefig(
        'plots/turbulent_kinetic_energy_x=6h.png', bbox_inches='tight')

    plt.show()