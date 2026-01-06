plate_len      = 80;       
plate_wid      = 60;       
plate_thk      = 3;        
uno_hole_diam  = 3.2;

uno_origin     = [5, 10];  

uno_hole_pts = [
    [0,   43.5],
    [50.5, 28],
    [50.5, 0]
];

mount_origin = [18, 15];

mount_pts  = [
    [0,   0],
    [44, 30],
    [0, 30],
    [44, 0]
];
module plate_body() {
    translate([0,0,0])
        cube([plate_len, plate_wid, plate_thk], center=false);
}

module drill_hole(x, y, d) {
    translate([x, y, -0.1]) 
        cylinder(h=plate_thk + 0.2, r=d/2, $fn=60);
}

module uno_holes() {
    for (pt = uno_hole_pts) {
        drill_hole(uno_origin[0] + pt[0], uno_origin[1] + pt[1], uno_hole_diam);
    }
}
module mount() {
    for (pt = mount_pts) {
        drill_hole(mount_origin[0] + pt[0], mount_origin[1] + pt[1], uno_hole_diam);
    }
}

module sensor() {

    block_size    = [5, 5, 12];
    pitch         = [15.5, 6.5];
    rows          = 2;
    cols          = 2;

    for (i = [0:cols-1]) {
        for (j = [0:rows-1]) {
            translate([i*pitch[0], j*pitch[1], 0])
                cube(block_size, center=false);
        }
    }
}
union(){
difference() {
    plate_body();
    uno_holes();
    mount();
}

translate([80,40.5,3])
rotate([0,0,110])
sensor();
translate([73,0.5,3])
rotate([0,0,70])
sensor();
}