`timescale 1ns / 1ps

module pipo_register_8bit_tb;
    reg clk;
    reg rst;
    reg en;
    reg [7:0] d;
    wire [7:0] q;

    pipo_register_8bit dut (
        .clk(clk),
        .rst(rst),
        .en(en),
        .d(d),
        .q(q)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    integer i;
    reg [7:0] expected;

    initial begin
        rst = 1;
        en = 0;
        d = 8'h00;
        expected = 8'h00;

        repeat (2) @(posedge clk);
        rst = 0;

        for (i = 0; i < 4; i = i + 1) begin
            en = 1;
            d = 8'h11 * (i + 1);
            expected = d;
            @(posedge clk);
            #1;
            if (q !== expected) begin
                $display("FAIL: load idx=%0d q=%0h expected=%0h", i, q, expected);
                $fatal;
            end
        end

        en = 0;
        d = 8'hAA;
        @(posedge clk);
        #1;
        if (q !== expected) begin
            $display("FAIL: hold q=%0h expected=%0h", q, expected);
            $fatal;
        end

        rst = 1;
        @(posedge clk);
        #1;
        if (q !== 8'h00) begin
            $display("FAIL: reset q=%0h expected=00", q);
            $fatal;
        end

        $display("PASS");
        $finish;
    end
endmodule

