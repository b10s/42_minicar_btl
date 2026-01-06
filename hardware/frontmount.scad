pcb_wid = 48;
pcb_len = 180;
pcb_thk = 2;

plate_wid = 140;
plate_thk = 2;
plate_len = 50;

lidar_hole_diam = 3;

mounts_wid = 6;
mounts_len = 30;

lidar_pts  = [
    [0,   28.2],
    [28.2, 28.2],
    [28.2, 0],
    [0, 0]
];

pcb_pts = [
    [5,  0],
    [5, 38]
];
module plate_body() {
    cube([plate_len, plate_wid, plate_thk], center=false);
}

module plate_body2() {
    cube([pcb_wid, pcb_wid + 10, plate_thk+1.99], center=false);
}

module plate_body3() {
    cube([pcb_wid+1, pcb_wid, plate_thk], center=false);
}


module drill_hole(x, y, d) {
    translate([x, y, -0.1]) 
        cylinder(h=plate_thk + 0.2, r=d/2, $fn=60);
}

module drill_mount(x, y) {
    translate([x, y, -0.1]) 
        cube([mounts_wid, mounts_len, plate_thk + 0.2]);
}

module drill_add(x, y) {
    translate([x, y, -0.1]) 
        cube([30, 45, plate_thk + 0.2]);
}


module lidar_holes() {
    for (pt = lidar_pts) {
        drill_hole(pt[0], pt[1], lidar_hole_diam);
    }
}

module pcb_holes() {
    for (pt = pcb_pts) {
        drill_hole(pt[0], pt[1], lidar_hole_diam);
    }
}


union(){
    difference(){
    translate([50,(plate_wid - pcb_wid)/2-5, 0])
        plate_body2();
    translate([55,(plate_wid - pcb_wid)/2, 2])
        plate_body3();
        pcb_holes();
    }
    difference() {
        plate_body();
        translate([5, 55.9, 0])
        lidar_holes();
        drill_mount(40,10);
        drill_mount(40,100);
        drill_add(-1, -1);
        drill_add(-1, 96);
    }
}

