`timescale 1ns / 1ps

module shift_register_4bit_tb;
    reg clk;
    reg rst;
    reg en;
    reg serial_in;
    wire [3:0] q;

    shift_register_4bit dut (
        .clk(clk),
        .rst(rst),
        .en(en),
        .serial_in(serial_in),
        .q(q)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    reg [7:0] pattern;
    reg [3:0] expected;
    integer i;

    initial begin
        rst = 1;
        expected = 4'b0000;
        en = 0;
        serial_in = 0;
        pattern = 8'b11010011;
        expected = 4'b0000;

        repeat (2) @(posedge clk);
        rst = 0;
        en = 1;

        for (i = 0; i < 8; i = i + 1) begin
            serial_in = pattern[i];
            expected = {expected[2:0], pattern[i]};
            @(posedge clk);
            #1;
            if (q !== expected) begin
                $display("FAIL: step=%0d q=%0b expected=%0b", i, q, expected);
                $fatal;
            end
        end

        en = 0;
        serial_in = 1'b0;
        @(posedge clk);
        #1;
        if (q !== expected) begin
            $display("FAIL: en low expected hold. q=%0b", q);
            $fatal;
        end

        rst = 1;
        @(posedge clk);
        #1;
        if (q !== 4'b0000) begin
            $display("FAIL: reset did not clear q=%0b", q);
            $fatal;
        end

        $display("PASS");
        $finish;
    end
endmodule

