`timescale 1ns / 1ps

module sequence_detector_101_tb;
    reg clk;
    reg rst;
    reg in_bit;
    wire detected;

    sequence_detector_101 dut (
        .clk(clk),
        .rst(rst),
        .in_bit(in_bit),
        .detected(detected)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    reg [15:0] stimulus;
    reg [15:0] expected;
    integer i;

    initial begin
        stimulus = 16'b1_0_1_1_0_1_0_1_0_0_1_0_1_0_1_0;
        expected = 16'b0_0_1_0_0_1_0_1_0_0_0_0_1_0_1_0;

        rst = 1;
        in_bit = 0;
        @(posedge clk);
        rst = 0;

        for (i = 15; i >= 0; i = i - 1) begin
            in_bit = stimulus[i];
            @(posedge clk);
            #1;
            if (detected !== expected[i]) begin
                $display("FAIL: step=%0d in=%0b detected=%0b expected=%0b", 15 - i, in_bit, detected, expected[i]);
                $fatal;
            end
        end

        $display("PASS");
        $finish;
    end
endmodule

