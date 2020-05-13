clear all
clc

% INPUTS
E  = [ 1e8, 1e26 ];
nu = [ 0.29, 0.29 ];
R  = 12.2474/2.0;
P  = 5.0e5; % Pressure on hemisphere's main diagonal
F = P * R * R * pi()

% PRELIMINARY CALCULATION
pi_3 = pi()^3;
E_ = 1 / ( (1 - nu(1)*nu(1))/E(1) + (1 - nu(2)*nu(2))/E(2) );

% Analytical Results
% radius of contact
a0 = (  (3 * P * pi() * R * R *R * (1-nu(1)*nu(1)))/(4 * E_)    )^(1/3);
% max contact pressure
p0 =  3 * P * R * R/(2.0 * a0 * a0);
% max vertical indentation
d0 = a0*a0 / R;
% vertical force at the center
f0 = E_ * (R*d0^3)^(1/2) * 4/3;

% Analytical Plot
n = 100;
x_max = a0;
y_max = 0.0;
xa = linspace( 0.0, x_max,  n );
ya = linspace( 0.0, y_max, n );
ra = ( xa.*xa + ya.*ya ).^(1/2);

pa = p0 * ( 1 - (ra.*ra)/(a0*a0) ).^0.5;
za = -(ra.^2)/(2*R);

fa = (-2/3)*p0*pi()*a0^2*( ( 1-( ra(2:end).^2 /a0^2 ) ).^(3/2) );

s = '';
s = horzcat( s, sprintf( '::: Analytical solution for Hertz Test ::: \n' ) );
s = horzcat( s, sprintf( 'a0 = %f \n', a0 ) );
s = horzcat( s, sprintf( 'p0 = %f \n', p0 ) );
s = horzcat( s, sprintf( 'd0 = %f \n', d0 ) );
s = horzcat( s, sprintf( 'f0 = %f \n', f0 ) );
clc
s

% Simulation coarse

p_coarse = [
0.00E+00	1.587046E+07
1.91E-01	1.572165E+07
3.82E-01	1.526366E+07
5.72E-01	1.445843E+07
7.62E-01	1.323046E+07
9.50E-01	1.145192E+07
1.14E+00	1.000699E+07
1.32E+00	2.272305E+06
];

z_coarse  = [
0.00E+00	-1.8946135e-16
1.91E-01	-0.0031857721
3.82E-01	-0.012716094
5.72E-01	-0.028510472
7.62E-01	-0.050436877
9.50E-01	-0.078314818
1.14E+00	-0.11191949
1.32E+00	-0.1509772
];

% Simulation remeshed
p_refined = [
0.	1.62858247750016e7
0.094565999999997	1.624356227507673e7
0.189131999999994	1.6116347814484665e7
0.283697999999991	1.59016012775817e7
0.378263999999988	1.5596285984001009e7
0.472829999999985	1.5196008334268067e7
0.567395999999982	1.4690661768122047e7
0.661961999999979	1.4067258652054664e7
0.756527999999976	1.3316359661763482e7
0.851093999999973	1.2407169854162924e7
0.94565999999997	1.1306147027066875e7
1.040225999999967	9.953311812642833e6
1.134791999999964	8.209135706348872e6
1.229357999999961	5.749801484978621e6
1.323923999999958	0.0
];

z_refined = [
0.0	0.0
0.094565999999997	-0.0003636307984865787
0.189131999999994	-0.0029960373775109704
0.283697999999991	-0.006730946766078518
0.378263999999988	-0.011777391438474307
0.472829999999985	-0.018038923088040622
0.567395999999982	-0.026387701339291362
0.661961999999979	-0.03559130717163208
0.756527999999976	-0.04692577807049404
0.851093999999973	-0.05942929714889923
0.94565999999997	-0.07341590719805802
1.040225999999967	-0.08821245097937946
1.134791999999964	-0.10492418702940491
1.229357999999961	-0.12317141827758461
1.323923999999958	-0.14317999489262173
];

%% Plotting
% Plot pressure
% plot( ra,      pa,      'b-', 'Analytical')
% plot( ps(:,1), ps(:,2), 'ko', 'Simulation')
% xlabel( 'x (m)' )
% ylabel( 'Contact normal traction (Pa)' )
% legend()
% grid()

% Plot vertical displacement
figure1 = figure(1)
plot( ra, za, 'b-','LineWidth',4)
hold on
plot( z_coarse(:,1), z_coarse(:,2), 'mo-')
hold on
plot( z_refined(:,1), z_refined(:,2), 'bo-')
xlabel( 'x [m]' )
ylabel( 'Vertical displacement [m]' )
legend('Analytical','Sim. Coarsed', 'Sim. Refined')
grid on
xlim([0,a0*1.05])
hold off

% Plot pressure distribution
figure2 = figure(2)
plot( ra, pa, 'b-','LineWidth',4)
hold on
plot( p_coarse(:,1), p_coarse(:,2), 'mo-')
hold on
plot( p_refined(:,1), p_refined(:,2), 'bo-')
xlabel( 'x [m]' )
ylabel( 'Pressure [N/m2]' )
legend('Analytical', 'Sim. Coarsed', 'Sim. Refined')
grid on
xlim([0,a0*1.05])
hold off

%% Calculate Error

za_erRcoarse = -(z_coarse(2:end,1).^2)/(2*R);
erRz_coarse = abs( (za_erRcoarse - z_coarse(2:end,2))./(za_erRcoarse) );

za_erRrefined = -(z_refined(2:end,1).^2)/(2*R);
erRz_refined = abs( (za_erRrefined - z_refined(2:end,2))./(za_erRrefined) );

figure3 = figure(3)
plot(z_coarse(2:end,1), erRz_coarse, 'mo-')
hold on
plot(z_refined(2:end,1), erRz_refined, 'bo-')
xlabel( 'x [m]' )
ylabel( 'Error displacement from analytical solution' )
legend('Sim. Coarsed','Sim. Refined')
xlim([0,a0*1.05])
grid on
hold off

pa_erRcoarse = p0 * ( 1 - (p_coarse(:,1).*p_coarse(:,1))/(a0*a0) ).^0.5;
erRp_coarse = abs( (pa_erRcoarse - p_coarse(:,2))./(pa_erRcoarse) );

pa_erRrefined = p0 * ( 1 - (p_refined(:,1).*p_refined(:,1))/(a0*a0) ).^0.5;
erRp_refined = abs( (pa_erRrefined - p_refined(:,2))./(pa_erRrefined) );

figure4 = figure(4)
plot(p_coarse(:,1), erRp_coarse, 'mo-')
hold on
plot(p_refined(:,1), erRp_refined, 'bo-')
xlabel( 'x [m]' )
ylabel( 'Error pressure from analytical solution' )
legend('Sim. Coarsed','Sim. Refined')
xlim([0,a0*1.05])
grid on
hold off

matlab2tikz('figurehandle',figure1,'filename','hertz1.tikz' ,'standalone', true);
matlab2tikz('figurehandle',figure2,'filename','hertz2.tikz' ,'standalone', true);
matlab2tikz('figurehandle',figure3,'filename','hertz3.tikz' ,'standalone', true);
matlab2tikz('figurehandle',figure4,'filename','hertz4.tikz' ,'standalone', true);
