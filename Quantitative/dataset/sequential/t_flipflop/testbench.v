`timescale 1ns / 1ps

module t_flipflop_tb;
    reg clk;
    reg rst;
    reg t;
    wire q;

    t_flipflop dut (
        .clk(clk),
        .rst(rst),
        .t(t),
        .q(q)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    reg expected;
    integer i;

    initial begin
        rst = 1;
        t = 0;
        expected = 0;

        repeat (2) @(posedge clk);
        rst = 0;

        // toggle for five cycles
        for (i = 0; i < 5; i = i + 1) begin
            t = 1;
            expected = ~expected;
            @(posedge clk);
            #1;
            if (q !== expected) begin
                $display("FAIL: toggle idx=%0d q=%0b expected=%0b", i, q, expected);
                $fatal;
            end
        end

        // hold for two cycles
        t = 0;
        repeat (2) begin
            @(posedge clk);
            #1;
            if (q !== expected) begin
                $display("FAIL: hold q=%0b expected=%0b", q, expected);
                $fatal;
            end
        end

        rst = 1;
        @(posedge clk);
        #1;
        if (q !== 1'b0) begin
            $display("FAIL: reset q=%0b expected=0", q);
            $fatal;
        end

        $display("PASS");
        $finish;
    end
endmodule

