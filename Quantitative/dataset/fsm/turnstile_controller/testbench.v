`timescale 1ns / 1ps

module turnstile_controller_tb;
    reg clk;
    reg rst;
    reg coin;
    reg push;
    wire locked;
    wire alarm;

    turnstile_controller dut (
        .clk(clk),
        .rst(rst),
        .coin(coin),
        .push(push),
        .locked(locked),
        .alarm(alarm)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    integer step;

    initial begin
        rst = 1;
        coin = 0;
        push = 0;

        @(posedge clk);
        rst = 0;

        // Initially locked
        @(posedge clk);
        #1;
        if (!locked || alarm) begin
            $display("FAIL: expected locked on reset");
            $fatal;
        end

        // Push without coin -> alarm, remain locked
        push = 1;
        @(posedge clk);
        push = 0;
        #1;
        if (!locked || !alarm) begin
            $display("FAIL: expected alarm on push without coin");
            $fatal;
        end

        // Coin inserted -> unlocked
        coin = 1;
        @(posedge clk);
        coin = 0;
        #1;
        if (locked || alarm) begin
            $display("FAIL: expected unlocked after coin");
            $fatal;
        end

        // Extra coin should keep unlocked
        coin = 1;
        @(posedge clk);
        coin = 0;
        #1;
        if (locked || alarm) begin
            $display("FAIL: expected stay unlocked with extra coin");
            $fatal;
        end

        // Push to go through -> lock again, no alarm
        push = 1;
        @(posedge clk);
        push = 0;
        #1;
        if (!locked || alarm) begin
            $display("FAIL: expected lock without alarm after valid push");
            $fatal;
        end

        $display("PASS");
        $finish;
    end
endmodule

