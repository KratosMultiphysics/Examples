import numpy as np 

fom_output = np.load("FOM/ExpectedOutput.npy")
galerkin_rom_output = np.load("ROM/ExpectedOutputROM.npy")
lspg_rom_output = np.load("LSPGROM/ExpectedOutputLSPGROM.npy")
pg_rom_output = np.load("PGROM/ExpectedOutputPGROM.npy")

galerkin_error = np.linalg.norm(galerkin_rom_output-fom_output)/np.linalg.norm(fom_output)
lspg_error = np.linalg.norm(lspg_rom_output-fom_output)/np.linalg.norm(fom_output)
pg_error = np.linalg.norm(pg_rom_output-fom_output)/np.linalg.norm(fom_output)
print("Galerkin error: ", galerkin_error)
print("LPSG error: ", lspg_error)
print("Petrov-Galerkin error: ", pg_error)