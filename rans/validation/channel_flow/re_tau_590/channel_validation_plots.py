import numpy, math
import matplotlib.pyplot as plt

plt.rcParams.update({'font.size': 22})

def get_column_index(headers, column_name):
    index = -1
    for header in headers:
        index += 1
        if column_name==header:
            return index

class Channel:
    def __init__(self, Re_tau, kinematic_viscosity, height, initial_y_plus):
        self.Re_tau = Re_tau
        self.kinematic_viscosity = kinematic_viscosity
        self.height = height
        self.initial_y_plus = initial_y_plus

        self.u_tau = 2.0 * self.Re_tau * self.kinematic_viscosity / self.height

        self.kratos_data = None
        self.kratos_headers = None
        self.dns_data_y_plus = None
        self.dns_data_u_plus = None
        self.dns_data_k_plus = None
        self.plot_header = ""
        self.dns_header = ""

    def ReadKratosCSVFile(self, file_name):
        self.kratos_data_file_name = file_name
        self.kratos_data = numpy.loadtxt(file_name, skiprows=1, delimiter=",")
        with open(file_name, "r") as file_input:
            self.kratos_headers = file_input.readline()[:-1].split(",")

        self.__modify_kratos_data()

    def __get_kratos_column_data(self, column_name):
        return self.kratos_data[:, get_column_index(self.kratos_headers, "\"" + column_name + "\"")]

    def __modify_kratos_data(self):
        y = self.__get_kratos_column_data("arc_length")
        y_plus = y * self.u_tau / self.kinematic_viscosity

        index = -1
        for y_plus_i in y_plus:
            index += 1
            if (y_plus_i >= self.initial_y_plus):
                self.kratos_data = self.kratos_data[index:,:]
                return

    def plot_u_plus(self):
        plt.figure(figsize=(12,9))
        plt.semilogx(self.dns_data_y_plus,
                     self.dns_data_u_plus,
                     "r-",
                     label=self.dns_header)

        u = self.__get_kratos_column_data("VELOCITY_Magnitude")
        u_plus = u / self.u_tau
        y = self.__get_kratos_column_data("arc_length")
        y_plus = y * self.u_tau / self.kinematic_viscosity

        plt.semilogx(y_plus,
                     u_plus,
                     "g--",
                     label=r"RANSModellingApplication $k-\epsilon$ high $Re$")

        plt.grid(True)
        plt.legend(loc="upper left")
        plt.xlabel(r"$y^+$")
        plt.ylabel(r"$u^+$")
        plt.title(r"Velocity Variation at $Re_\tau=%0.0f$" % (self.Re_tau))
        plt.savefig("plots/full_channel_re_tau_" + str(int(self.Re_tau)) + "_u_plus.png", bbox_inches="tight")

    def plot_turbulent_kinetic_energy(self):
        plt.figure(figsize=(12,9))
        plt.plot(self.dns_data_y_plus,
                 self.dns_data_k_plus,
                 "r-",
                 label=self.dns_header)

        k = self.__get_kratos_column_data("TURBULENT_KINETIC_ENERGY")
        k_plus = k / (self.u_tau * self.u_tau)
        y = self.__get_kratos_column_data("arc_length")
        y_plus = y * self.u_tau / self.kinematic_viscosity

        plt.plot(y_plus,
                 k_plus,
                 "g--",
                 label=r"RANSModellingApplication $k-\epsilon$ high $Re$")

        plt.grid(True)
        plt.legend(loc="upper right")
        plt.xlabel(r"$y^+$")
        plt.ylabel(r"$k^+$")
        plt.title(r"Turbulent Kinetic Energy Variation at $Re_\tau=%0.0f$" % (self.Re_tau))
        plt.savefig("plots/full_channel_re_tau_" + str(int(self.Re_tau)) + "_k_plus.png", bbox_inches="tight")

    def plot_stresses(self):
        plt.figure(figsize=(12,9))

        nu_t = self.__get_kratos_column_data("TURBULENT_VISCOSITY")
        du_dy = self.__get_kratos_column_data("Gradients_1")
        y = self.__get_kratos_column_data("arc_length")
        y_plus = y * self.u_tau / self.kinematic_viscosity

        u_tau_2 = self.u_tau * self.u_tau

        reynolds_stress = -nu_t * du_dy / u_tau_2
        viscous_stress = -self.kinematic_viscosity * du_dy / u_tau_2
        total_stress = reynolds_stress + viscous_stress

        plt.plot(total_stress,
                 y_plus,
                 "g--",
                 label=r"Total stress $\left[-\frac{\left(\nu + \nu_t\right)}{u_\tau^2}\frac{du}{dy}\right]$")

        plt.plot(viscous_stress,
                 y_plus,
                 "b-.",
                 label=r"Viscous stress $\left[-\frac{\nu}{u_\tau^2}\frac{du}{dy}\right]$")

        plt.plot(reynolds_stress,
                 y_plus,
                 "c:",
                 label=r"Reynolds stress $\left[-\frac{\nu_t}{u_\tau^2}\frac{du}{dy}\right]$")

        plt.plot([-1.0, 0.0], [0.0, self.Re_tau], "r-", label="Reference")

        plt.grid(True)
        plt.legend(loc="upper left")
        plt.ylabel(r"$y^+$")
        plt.xlabel("Stress")
        plt.title(r"Stress Variation at $Re_\tau=%0.0f$" % (self.Re_tau))
        plt.savefig("plots/full_channel_re_tau_" + str(int(self.Re_tau)) + "_stress.png", bbox_inches="tight")

def channel_590():
    channel = Channel(590.0, 1e-2, 2.0, 12.0)
    channel.ReadKratosCSVFile("line_outputs/x=3.14.csv")
    dns_data = numpy.loadtxt("dns_data_Moser/profiles/chan590.means")
    channel.dns_data_y_plus = dns_data[:, 1]
    channel.dns_data_u_plus = dns_data[:, 2]

    dns_data = numpy.loadtxt("dns_data_Moser/profiles/chan590.reystress")
    channel.dns_data_k_plus = 0.5*(dns_data[:, 2] + dns_data[:, 3] + dns_data[:, 4])

    channel.dns_header = r"$Moser$ $et$ $al.$"

    channel.plot_u_plus()
    channel.plot_turbulent_kinetic_energy()
    channel.plot_stresses()

if __name__=="__main__":
    channel_590()
    plt.show()