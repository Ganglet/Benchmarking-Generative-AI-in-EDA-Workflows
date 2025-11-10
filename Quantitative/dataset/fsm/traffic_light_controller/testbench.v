`timescale 1ns / 1ps

module traffic_light_controller_tb;
    reg clk;
    reg rst;
    wire [2:0] ns_light;
    wire [2:0] ew_light;

    traffic_light_controller dut (
        .clk(clk),
        .rst(rst),
        .ns_light(ns_light),
        .ew_light(ew_light)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    localparam RED    = 3'b100;
    localparam YELLOW = 3'b010;
    localparam GREEN  = 3'b001;

    reg [2:0] ns_expected [0:11];
    reg [2:0] ew_expected [0:11];
    integer i;

    initial begin
        ns_expected[0]  = GREEN; ew_expected[0]  = RED;
        ns_expected[1]  = GREEN; ew_expected[1]  = RED;
        ns_expected[2]  = GREEN; ew_expected[2]  = RED;
        ns_expected[3]  = YELLOW; ew_expected[3] = RED;
        ns_expected[4]  = YELLOW; ew_expected[4] = RED;
        ns_expected[5]  = RED;   ew_expected[5]  = GREEN;
        ns_expected[6]  = RED;   ew_expected[6]  = GREEN;
        ns_expected[7]  = RED;   ew_expected[7]  = GREEN;
        ns_expected[8]  = RED;   ew_expected[8]  = YELLOW;
        ns_expected[9]  = RED;   ew_expected[9]  = YELLOW;
        ns_expected[10] = GREEN; ew_expected[10] = RED;
        ns_expected[11] = GREEN; ew_expected[11] = RED;

        rst = 1;
        @(posedge clk);
        rst = 0;

        for (i = 0; i < 12; i = i + 1) begin
            @(posedge clk);
            #1;
            if (ns_light !== ns_expected[i] || ew_light !== ew_expected[i]) begin
                $display("FAIL: cycle=%0d ns=%0b ew=%0b expected_ns=%0b expected_ew=%0b", i, ns_light, ew_light, ns_expected[i], ew_expected[i]);
                $fatal;
            end
        end

        $display("PASS");
        $finish;
    end
endmodule

