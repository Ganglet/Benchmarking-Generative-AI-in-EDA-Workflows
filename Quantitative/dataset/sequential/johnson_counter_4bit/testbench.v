`timescale 1ns / 1ps

module johnson_counter_4bit_tb;
    reg clk;
    reg rst;
    reg en;
    wire [3:0] q;

    johnson_counter_4bit dut (
        .clk(clk),
        .rst(rst),
        .en(en),
        .q(q)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    reg [3:0] expected [0:7];
    integer idx;

    initial begin
        expected[0] = 4'b0000;
        expected[1] = 4'b1000;
        expected[2] = 4'b1100;
        expected[3] = 4'b1110;
        expected[4] = 4'b1111;
        expected[5] = 4'b0111;
        expected[6] = 4'b0011;
        expected[7] = 4'b0001;

        rst = 1;
        en = 0;
        idx = 0;

        repeat (2) @(posedge clk);
        rst = 0;
        en = 1;

        for (idx = 0; idx < 8; idx = idx + 1) begin
            @(posedge clk);
            #1;
            if (q !== expected[idx]) begin
                $display("FAIL: idx=%0d q=%0b expected=%0b", idx, q, expected[idx]);
                $fatal;
            end
        end

        en = 0;
        @(posedge clk);
        #1;
        if (q !== expected[7]) begin
            $display("FAIL: hold expected %0b got %0b", expected[7], q);
            $fatal;
        end

        rst = 1;
        @(posedge clk);
        #1;
        if (q !== 4'b0000) begin
            $display("FAIL: reset expected 0000 got %0b", q);
            $fatal;
        end

        $display("PASS");
        $finish;
    end
endmodule

